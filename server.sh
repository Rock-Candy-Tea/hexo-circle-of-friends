#!/bin/bash
pip3 install -r ./hexo_circle_of_friends/requirements.txt

### 通用配置
export LINK="https://www.yyyzyyyz.cn/link/"
export EXPOSE_PORT=8000
#export PROXY=""
### leancloud配置
export APPID=""
export APPKEY=""
### mysql配置
#export MYSQL_USERNAME=""
#export MYSQL_PASSWORD=""
#export MYSQL_IP=""
#export MYSQL_DB=""

nohup python3 -u ./hexo_circle_of_friends/run.py > /tmp/crawler.log 2>&1 &
nohup python3 -u ./api/main.py > /tmp/api.log 2>&1 &
while [[ true ]]; do
    sleep 10
done