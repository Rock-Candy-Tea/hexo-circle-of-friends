#!/bin/bash
# Start the first process
nohup python3 -u ./hexo_circle_of_friends/run.py > /tmp/crawler_stdout.log 2>&1 &
ps aux |grep run |grep -q -v grep
PROCESS_1_STATUS=$?
echo "run.py status..."
echo $PROCESS_1_STATUS
if [ $PROCESS_1_STATUS -ne 0 ]; then
echo "Failed to start run.py: $PROCESS_2_STATUS"
exit $PROCESS_1_STATUS
fi
sleep 5
# Start the second process
nohup python3 -u ./api/main.py > /tmp/api_stdout.log 2>&1 &
ps aux |grep main |grep -q -v grep
PROCESS_2_STATUS=$?
echo "main.py status..."
echo $PROCESS_2_STATUS
if [ $PROCESS_2_STATUS -ne 0 ]; then
echo "Failed to start main.py: $PROCESS_2_STATUS"
exit $PROCESS_2_STATUS
fi
# 每隔60秒检查进程是否运行
while sleep 60; do
ps aux |grep run |grep -q -v grep
PROCESS_1_STATUS=$?
ps aux |grep main |grep -q -v grep
PROCESS_2_STATUS=$?
# If the greps above find anything, they exit with 0 status
# If they are not both 0, then something is wrong
if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
echo "One of the processes has already exited."
exit 1
fi
done