FROM python:3.8
MAINTAINER yyyz
COPY . /
### 在这里配置环境变量
### 通用配置
ENV LINK="https://www.yyyzyyyz.cn/link/"
ENV RUN_PER_HOURS=6
#ENV PROXY=""
### leancloud配置
ENV APPID=""
ENV APPKEY=""
### mysql配置
#ENV MYSQL_USERNAME=""
#ENV MYSQL_PASSWORD=""
#ENV MYSQL_IP=""
#ENV MYSQL_DB=""
EXPOSE 8000
WORKDIR /
RUN cd ./hexo_circle_of_friends && pip3 install -r requirements.txt -i https://pypi.douban.com/simple/
CMD bash ./docker.sh



