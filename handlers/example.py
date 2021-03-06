#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/6
# CreatTIME : 20:10 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
"""
关于全局配置文件中，变量的使用示例
"""
# 暂时为了防止与原有config变量冲突而命名为configs
from handlers.coreSettings import configs as config

# settings.py变量的使用
print(config.BASE_PATH)

# 载入的yml文件的使用
print(config.yml)

if __name__ == '__main__':
    pass
