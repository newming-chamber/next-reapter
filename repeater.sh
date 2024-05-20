#!/bin/bash

echo "Start Crontab : $(date '+%Y-%m-%d %H:%M:%S')" >> ~/next-repeater/cron.log
output=$(/usr/bin/python3 ~/next-repeater/repeater.py)
echo "Result $output" >> ~/next-repeater/cron.log
