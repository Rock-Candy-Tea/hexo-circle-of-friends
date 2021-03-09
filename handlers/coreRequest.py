#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/9
# CreatTIME : 14:23 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

import time

from component.getThread import thread_callback
from component.getWeb import get_data
from handlers.coreSettings import configs as config

class reRequest(object):
    def __init__(self):
        self.timeout = config.TIMEOUT
        self.reTry = config.RETRY_MAX
        self.verify = config.VERIFY
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
            t = thread_callback(get_data, (u, headers, timeout, reTry, verify))
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