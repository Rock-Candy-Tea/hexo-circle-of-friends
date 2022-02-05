#!/bin/bash
cd ./hexo_circle_of_friends && pip3 install -r requirements.txt

### 通用配置
export LINK="https://www.yyyzyyyz.cn/link/"
export EXPOSE_PORT=8000
# ENV PROXY=""
### leancloud配置
export APPID=""
export APPKEY=""
### mysql配置
#export MYSQL_USERNAME=""
#export MYSQL_PASSWORD=""
#export MYSQL_IP=""
#export MYSQL_DB=""

nohup python -u ./hexo_circle_of_friends/run.py > /tmp/crawler.log 2>&1 &
nohup python -u ./api/main.py > /tmp/api.log 2>&1 &
