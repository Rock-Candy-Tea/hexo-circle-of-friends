FROM yyyzyyyz/centos-py
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

# docker login
# docker build -t yyyzyyyz/fcircle .
# docker push yyyzyyyz/fcircle
# ---------------------------------------------- #
# export DOCKER_CLI_EXPERIMENTAL=enabled
# docker run --rm --privileged docker/binfmt:66f9012c56a8316f9244ffd7622d7c21c1f6f28d
# docker buildx create --use --name mybuilder
# docker buildx inspect mybuilder --bootstrap
# docker buildx build -t yyyzyyyz/fcircle --platform=linux/arm,linux/arm64,linux/amd64 . --push