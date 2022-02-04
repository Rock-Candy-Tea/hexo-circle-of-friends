# -*- coding:utf-8 -*-
# Author：yyyz
import sys
import os
basedir= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(sys.path.append(basedir))

from hexo_circle_of_friends.settings import *
def initsettings(setting):
    if DATABASE == 'leancloud':
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.leancloud_pipe.LeancloudPipeline"] = 300
    elif DATABASE == 'mysql' or DATABASE== "sqlite":
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.sql_pipe.SQLPipeline"] = 300

