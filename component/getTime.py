#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理时间相关作用的组件
"""
import re


# 时间查找(中文、标准）
def time_zero_plus(tempStr:str):
    """
    时间查找(中文、标准）
    :param tempStr: str,
    :return: str
    """
    if len(tempStr) < 2:
        tempStr = '0' + tempStr
    return tempStr


def find_time(tempStr:str):
    time = ''
    try:
        timere = re.compile(r'[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}', re.S)
        time = re.findall(timere, tempStr)[0]
        timelist = time.split('-')
        time = timelist[0] + '-' + time_zero_plus(timelist[1]) + '-' + time_zero_plus(timelist[2])
        print('获得标准时间', time)
    except:
        try:
            timere_ch = re.compile(r'[0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日', re.S)
            time_ch = re.findall(timere_ch, tempStr)[0]
            print('找到中文时间', time_ch)
            year = time_ch.split('年')[0].strip()
            month = time_zero_plus(time_ch.split('年')[1].split('月')[0].strip())
            day = time_zero_plus(time_ch.split('年')[1].split('月')[1].split('日')[0].strip())
            time = year + '-' + month + '-' + day
            print('获得标准时间', time)
        except:
            print('没找到符合要求的时间')
            time = ''
    return time


if __name__ == '__main__':
    pass
