#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/6
# CreatTIME : 18:23 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
"""
全局设置 控件
"""
import settings
import os
import yaml


class loading_configs(object):
    """
    载入配置文件
    """

    def __init__(self):
        # 读取settings文件所有变量
        # 并将变量初始化为loading_configs的内部变量
        temp = [i if i.isupper() else None for i in dir(settings)]
        temp = list(filter(None, temp))
        for k in temp:
            setattr(self, k, getattr(settings, k))

        # 读取yml文件
        with open(os.path.join(self.BASE_PATH, '_config.yml'), 'r', encoding='utf-8') as f:
            self.yml = yaml.load(f.read(), Loader=yaml.FullLoader)


# 实例化
configs = loading_configs()

if __name__ == '__main__':
    pass
    # temp = [i if i.isupper() else None for i in dir(settings)]
    # temp = list(filter(None, temp))
    # config = loading_configs(temp)
    # print(config.BASE_PATH)
