#!/bin/bash
cd /home/pi/prog/capcamsockserver
sudo mount --bind /media/pi/4d19ec75* /mnt/hdd1
python camserver.py 3300 0 ; python camserver.py 3301 1 ;
python camserver.py 3302 2 &
python camserver.py 3303 3 &
