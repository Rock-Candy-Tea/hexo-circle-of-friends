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
import platform


class loading_configs(object):
    """
    载入配置文件
    """

    def __init__(self):
        # 初始值
        self.BASE_PATH = None
        self.DEBUG = None

        # 读取settings文件所有变量
        # 并将变量初始化为loading_configs的内部变量
        temp = [i if i.isupper() else None for i in dir(settings)]
        temp = list(filter(None, temp))
        for k in temp:
            setattr(self, k, getattr(settings, k))

        # 初始化自检
        self.debug_check()

        # 读取yml文件(兼容代码)
        with open(os.path.join(self.BASE_PATH, '_config.yml'), 'r', encoding='utf-8') as f:
            self.yml = yaml.load(f.read(), Loader=yaml.FullLoader)



    def debug_check(self) -> None:
        """
        调试模式自检

        考虑到可能开了debug模式开发时忘记关闭的情况。
        :return: None
        """
        if self.DEBUG == True or not self.DEBUG:
            print("当前设置为 debug 模式")
            if platform.system().lower() == 'windows':
                self.DEBUG = True
            elif platform.system().lower() == 'linux':
                print("检测运行环境为linux,调整非debug模式")
                self.DEBUG = False
            else:
                self.DEBUG = False
        else:
            self.DEBUG = False


# 实例化
configs = loading_configs()

if __name__ == '__main__':
    pass
    # temp = [i if i.isupper() else None for i in dir(settings)]
    # temp = list(filter(None, temp))

    config = loading_configs()
    print(config.debug_check)
