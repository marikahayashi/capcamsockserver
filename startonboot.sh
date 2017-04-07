#!/bin/bash
if test `pgrep -f camserver.py | wc -l` -eq 0 ; then
    echo "1"
    export DISPLAY=:0.0
    cd /home/pi/prog/capcamsockserver/
    bash startserver.sh >> stdout.log 2>> errout.log
elif test `pgrep -f camserver.py | wc -l` -lt 4 ; then
    echo "2"
    bash /home/pi/prog/capcamsockserver/stopserver.sh
fi
echo "3"
