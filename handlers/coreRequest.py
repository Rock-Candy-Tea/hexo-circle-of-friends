#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/9
# CreatTIME : 14:23 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
"""
基于getWeb组件封装的多线程请求处理
"""

import time

from component.getThread import thread_callback
from component.getWeb import get_data
from handlers.coreSettings import configs

class reRequest(object):
    def __init__(self):
        self.timeout = configs.TIMEOUT
        self.reTry = configs.RETRY_MAX
        self.verify = configs.SSL
        self.headers = None

    def thread_load_web(self, urls,  inspectStr=None):
        threads = []
        resData = {}
        headers = self.headers
        timeout = self.timeout
        reTry = self.reTry
        verify = self.verify
        for u in urls:
            # 进程列表生成
            # t = thread_callback(get_data, (u, headers, timeout, reTry, verify))
            t = thread_callback(get_data, (u, headers, timeout, verify))
            threads.append(t)
            resData[u] = None

        for thread in threads:
            thread.start()
            time.sleep(3)

        for i, thread in enumerate(threads):
            thread.join()
            resData[urls[i]] = thread.get_result()
            # # 进度计算
            # info = '[%s/%s]' % (i + 1, len(urls))
            # logger.info(info)
        return resData

# 使用示范
if __name__ == '__main__':
    urls = ["www.baidu.com", "www.bilibili.com"]
    request = reRequest()
    res = request.thread_load_web(urls)
    # print(res)