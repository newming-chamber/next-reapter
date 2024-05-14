#!/bin/bash

echo "Start Crontab : $(date '+%Y-%m-%d %H:%M:%S')" >> /home/hankookilbo/next-repeater/cron.log
output=$(/usr/bin/python3 /home/hankookilbo/next-repeater/repeater.py)
echo "Result $output" >> /home/hankookilbo/next-repeater/cron.log
