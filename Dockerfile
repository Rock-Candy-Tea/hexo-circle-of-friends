FROM centos-py:latest
MAINTAINER yyyz
EXPOSE 8000
WORKDIR /home/fcircle_src/
ADD . /home/fcircle_src/
ARG PIP=/usr/bin/pip3
ENV TimeZone=Asia/Shanghai
ENV BASEPATH=/home/fcircle_src/
ENV PYTHONPATH=/home/fcircle_src/
RUN $PIP install -r ./hexo_circle_of_friends/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
&& ln -snf /usr/share/zoneinfo/$TimeZone /etc/localtime && echo $TimeZone > /etc/timezone