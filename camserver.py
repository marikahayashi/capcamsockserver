#!/usr/bin/env python
# -*- coding:utf-8 -*-

import SocketServer
import cv2
import numpy
import socket
import sys
import threading
import time
from datetime import datetime
import os
import commands
import netifaces
import ConfigParser
import signal

g_capture = None
g_frame = None
g_lock = threading.Lock()
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480

class TCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global g_lock, g_frame
        if g_frame is None:
            return
        sgnl = signal.signal(signal.SIGINT, signal.SIG_IGN)
        g_lock.acquire()
        jpeg_string = cv2.imencode('.jpeg', g_frame, (cv2.IMWRITE_JPEG_QUALITY, self.server.jpeg_quality))[1].tostring()
        g_lock.release()
        signal.signal(signal.SIGINT, sgnl)
        self.request.send(jpeg_string)


class CamCapTCPServer(SocketServer.TCPServer):
    jpeg_quality = 30
    

class ReadFrameThread(threading.Thread):
    def __init__(self):
        super(ReadFrameThread, self).__init__()
        self.video_number = 0
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()
        
    def run(self):
        global g_frame, g_capture
        while not self.stop_event.is_set():
            video_devname = '/dev/video' + str(self.video_number)
            command = 'if [ -e ' + video_devname + ' ]; then\necho \'0\'\nelse\necho \'1\'\nfi'
            if (commands.getoutput(command) != '0'):
                open_camera(self.video_number)
                continue
            try:
                g_lock.acquire()
                ret1, g_frame = g_capture.read()
                g_lock.release()
            except:
                pass


class ShowImgThread(threading.Thread):
    def __init__(self):
        super(ShowImgThread, self).__init__()
        self.interval = 0
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()
        
    def run(self):
        global g_frame
        while not self.stop_event.is_set():
            stime = time.time()
            if (g_frame is None):
                continue
            g_lock.acquire()
            cv2.imshow('cap', g_frame)
            g_lock.release()
            cv2.waitKey(1)
            #if (cv2.waitKey(1) & 0xff) == ord('q'):
            #    cv2.destroyAllWindows()
            #    break
            etime = time.time()
            rtime = self.interval - (etime - stime)
            #print "rtime = %s" % rtime
            if (rtime < 0):
                pass
            else:
                time.sleep(rtime)
        

class SaveImgThread(threading.Thread):
    def __init__(self):
        super(SaveImgThread, self).__init__()
        self.video_number = 0
        self.interval = 0
        self.save_folder_name = ''
        self.width = CAPTURE_WIDTH
        self.height = CAPTURE_HEIGHT
        self.jpeg_quality = 30
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()
    
    def run(self):
        global g_lock, g_frame
        if (self.width != CAPTURE_WIDTH) or (self.height != CAPTURE_HEIGHT):
            resize_flag = True
        else:
            resize_flag = False
        while not self.stop_event.is_set():
            stime = time.time()
            if (g_frame is None):
                continue
            try:
                nowtime = datetime.now()
                os.makedirs(self.save_folder_name + nowtime.strftime("/%Y-%m-%d/video") + str(self.video_number))
            except OSError:
                pass
            fname = self.save_folder_name + nowtime.strftime("/%Y-%m-%d/video") + str(self.video_number) + nowtime.strftime("/%H-%M-%S.jpg")
            print fname
            if (resize_flag):
                g_lock.acquire()
                resized_frame = cv2.resize(g_frame, (self.width, self.height))
                g_lock.release()
                cv2.imwrite(fname, resized_frame, (cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality))
            else:
                g_lock.acquire()
                cv2.imwrite(fname, g_frame, (cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality))
                g_lock.release()
            etime = time.time()
            rtime = self.interval - (etime - stime)
            #print "rtime = %s" % rtime
            if (rtime < 0):
                pass
            else:
                time.sleep(rtime)


def open_camera(video_number):
    global g_capture
    print "opening camera..",
    while True:
        if g_capture:
            g_capture.release()
        g_capture = cv2.VideoCapture(video_number)
        if g_capture.isOpened():
            print "opened camera #%s" % video_number
            break
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    g_capture.set(3, CAPTURE_WIDTH)
    g_capture.set(4, CAPTURE_HEIGHT)


def main():
    if (len(sys.argv) != 3):
        print "please set two arguments: port video_number"
        return
    inifile = ConfigParser.SafeConfigParser()
    inifile.read('./camserver.ini')
    addr = None
    for iface_name in netifaces.interfaces():
        if iface_name == 'wlan0':
            iface_data = netifaces.ifaddresses(iface_name)
            afnet = iface_data.get(netifaces.AF_INET)
            addr = afnet[0]['addr']
    if addr is None:
        perror('Error: no network connection')
        sys.exit()
    port = int(sys.argv[1])
    video_number = int(sys.argv[2])
    print "IPaddr=%s, port=%s, video_number=%s" % (addr, port, video_number)

    open_camera(video_number)

    readframethread = ReadFrameThread()
    readframethread.setDaemon(True)
    readframethread.video_number = video_number
    readframethread.start()

    saveimgthread = SaveImgThread()
    saveimgthread.setDaemon(True)
    saveimgthread.video_number = video_number
    saveimgthread.interval = float(inifile.get('main', 'interval_save'))
    saveimgthread.save_folder_name = inifile.get('main', 'save_folder_name')
    saveimgthread.height = int(inifile.get('main', 'save_resolution_height'))
    saveimgthread.width = int(inifile.get('main', 'save_resolution_width'))
    saveimgthread.set_jpeg_quality = int(inifile.get('main', 'save_jpeg_quality'))
    saveimgthread.start()

    showimgthread = ShowImgThread()
    showimgthread.setDaemon(True)
    showimgthread.interval = float(inifile.get('main', 'interval_show'))
    showimgthread.start()
    #SocketServer.TCPServer.allow_reuse_address = True
    #server = SocketServer.TCPServer((addr, port), TCPHandler)

    CamCapTCPServer.allow_reuse_address = True
    CamCapTCPServer.jpeg_quality = int(inifile.get('main', 'socket_jpeg_quality'))
    server = CamCapTCPServer((addr, port), TCPHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.shutdown()
    readframethread.stop()
    saveimgthread.stop()
    showimgthread.stop()

if __name__ == '__main__':
    main()
