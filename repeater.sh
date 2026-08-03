#!/bin/bash

# 크론이 1분 주기이므로 이전 실행이 끝나지 않았으면 이번 실행은 건너뛴다.
# 락 파일은 계정별로 분리한다 (언론사마다 다른 계정으로 실행됨).
LOCKFILE="/tmp/next-repeater-$(whoami).lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
    echo "SKIP Crontab (already running) : $(date '+%Y-%m-%d %H:%M:%S')" >> ~/next-repeater/cron.log
    exit 0
fi

echo "Start Crontab : $(date '+%Y-%m-%d %H:%M:%S')" >> ~/next-repeater/cron.log
output=$(/usr/bin/python3 ~/next-repeater/repeater.py)
echo "Result $output" >> ~/next-repeater/cron.log
echo "END Crontab : $(date '+%Y-%m-%d %H:%M:%S')" >> ~/next-repeater/cron.log
