# -*- coding:utf-8 -*-
# Author：yyyz
import os

while 1:
    r = input(
        "欢迎使用简单傻瓜式管理工具，请修改好settings.py和对应的环境变量之后，选择部署方式：\n——————————————————————————————————\n| 1、server | 2、docker | q、退出 |\n——————————————————————————————————\n")
    if r == "1":
        r = input(
            "请选择：\n——————————————————————————————————\n| 1、部署 | 2、取消部署 | q、退出 |\n——————————————————————————————————\n")
        if r == "1":
            os.system("chmod a+x server.sh && ./server.sh")
            print("已部署！")
        elif r == "2":
            os.system("ps -ef | grep python3 -u | grep -v grep | awk '{print $2}' | xargs kill -9")
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
