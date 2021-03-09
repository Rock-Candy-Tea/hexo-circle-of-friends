#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/9
# CreatTIME : 13:31 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
"""
线程器
"""
import threading


class thread_callback(threading.Thread):
    def __init__(self, func, args):
        super(thread_callback, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None
