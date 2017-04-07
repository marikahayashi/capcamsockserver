#!/bin/bash
cd /home/pi/prog/capcamsockserver
/bin/umount /mnt/hdd1
/bin/mount --bind /media/pi/4d19ec75-2f7a-4fef-bcfe-07ae100ad892 /mnt/hdd1
/usr/bin/python /home/pi/prog/capcamsockserver/camserver.py 3300 0 &
/usr/bin/python /home/pi/prog/capcamsockserver/camserver.py 3301 1 &
/usr/bin/python /home/pi/prog/capcamsockserver/camserver.py 3302 2 &
/usr/bin/python /home/pi/prog/capcamsockserver/camserver.py 3303 3 &

