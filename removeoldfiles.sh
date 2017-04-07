#!/bin/bash
#cd ~/prog/camcapsock/data
cd /mnt/hdd1/snapshots
rm -rf `date -I -d '90 days ago'`
cd -
