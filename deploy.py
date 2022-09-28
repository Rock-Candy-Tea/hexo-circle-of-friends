# -*- coding:utf-8 -*-
# Author：yyyz
import json
import os


def server_deploy():
    server_sh = """
    #!/bin/bash
    BASE_PATH=$(cd $(dirname $0); pwd)
    export BASE_PATH
    export PYTHONPATH=${PYTHONPATH}:${BASE_PATH}
    pip3 install -r ${BASE_PATH}/hexo_circle_of_friends/requirements.txt -i https://pypi.douban.com/simple/
    """
    if os.path.exists("env.json"):
        with open("env.json", "r") as f:
            envs = json.load(f)
    else:
        envs = {}

    with open("temp.sh", "w") as f:
        for name, value in envs.items():
            if value is not None:
                server_sh += f"export {name}={value}\n"
        server_sh += """
        nohup python3 -u ${BASE_PATH}/hexo_circle_of_friends/run.py > /tmp/crawler_stdout.log 2>&1 &
        nohup python3 -u ${BASE_PATH}/api/main.py > /tmp/api_stdout.log 2>&1 &
            """
        f.write(server_sh.strip())
    os.system("chmod a+x temp.sh && ./temp.sh && rm -f temp.sh")


while 1:
    r = input(
        "欢迎使用部署工具，选择部署方式：\n——————————————————————————————————\n| 1、server | 2、docker | q、退出 "
        "|\n——————————————————————————————————\n")
    if r == "1":
        r = input(
            "请选择：\n——————————————————————————————————\n| 1、部署 | 2、取消部署 | q、退出 |\n——————————————————————————————————\n")
        if r == "1":
            server_deploy()
            print("已部署！")
        elif r == "2":
            os.system("ps -ef | egrep 'python3 -u|python3 -c' | grep -v grep | awk '{print $2}' | xargs kill -9")
        elif r == "q":
            print("再见！")
            break
        else:
            print("输入错误~")
    elif r == "2":
        r = input(
            "请选择：\n——————————————————————————————————\n| 1、部署 | 2、取消部署 | q、退出 |\n——————————————————————————————————\n")
        if r == "1":
            os.system("docker build -t fcircle . && docker run -di --name circle -p 8000:8000 -v /tmp/:/tmp/ fcircle")
            print("已部署！")
        elif r == "2":
            os.system("docker stop circle && docker rm circle && docker rmi fcircle")
        elif r == "q":
            print("再见！")
            break
        else:
            print("输入错误~")
    elif r == "q":
        print("再见！")
        break
    else:
        print("输入错误~")
