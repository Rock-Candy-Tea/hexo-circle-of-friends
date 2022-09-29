# -*- coding:utf-8 -*-
# Author：yyyz
from datetime import datetime, timedelta
import re

today_parsed = datetime.utcnow() + timedelta(hours=8)


# 时间格式检查
def format_check(*args):
    for time in args:
        if not re.match("^\d{4}-\d{2}-\d{2}$", time):
            # 时间不是xxxx-xx-xx格式，丢弃
            return
    return True


# 内容检查
def content_check(*args):
    for time in args:
        res = today_parsed - datetime.strptime(time, "%Y-%m-%d")
        if res.days < 0:
            # 大于当前时间
            return
    return True


# 时间比较
def time_compare(checked_time, days):
    """
    用于检查待检测时间距今是否超过指定天数
    :param checked_time: 需要检查的时间
    :param days: 指定天数
    :return:
    """
    # 计算差值
    res = today_parsed - datetime.strptime(checked_time, "%Y-%m-%d")
    if res.days <= days:
        # 未超过
        return False
    else:
        return True


def format_time(times):
    """
    将传入的时间列表格式化
    :param times: 时间列表
    """
    try:
        # xxxx-x-x
        for i, time in enumerate(times):
            times[i] = datetime.strptime(time, "%Y-%m-%d").strftime('%Y-%m-%d')
    except:
        try:
            # 2021-11-12T01:24:06.000Z
            for i, time in enumerate(times):
                times[i] = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.000Z").strftime('%Y-%m-%d')
        except:
            # xxxx年xx月xx日
            for i, time in enumerate(times):
                times[i] = re.sub("(\d{4})年(\d{2})月(\d{2})日$", r'\1-\2-\3', time)
