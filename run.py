#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/8
# CreatTIME : 15:06 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
"""
主程序

业务流程：
主程序-->（处理器handlers）控件—->组件(component)

组件作为最底层，单向调用。
处理器可以调用组件，组件不可以调用处理里代码块。
避免产生双向调用执行流程不清。

处理器之间，不能互相调用。
避免出现处理器相互依赖，做到移除单一处理器时，不会导致其他处理器出错。
(特例：coreSettings.py，其他处理器可以单向调用coreSettings.py的值，
但coreSettings.py不能调用其他处理器的函数/类来处理)。
处理器避免直接调用外部settings.py里的参数，而是使用coreSettings.py来调用设置的值。
如要全局设置中的值，由coreSettings.py处理器统筹，使调用收束。

主程序
只负责：
调用处理器；
程序的整体执行流程；
打印执行信息.

todo:
request_data 组件化
request_data 多线程
theme 组件化

"""
from operator import itemgetter
import leancloud
import sys

# 组件
from theme.butterfly import butterfly
from theme.matery import matery
from theme.volantis import volantis

# 处理器
from handlers.coreSettings import configs
from handlers.coreLink import delete_same_link
from handlers.coreLink import block_link
from handlers.coreLink import kang_api
from handlers.coreLink import github_issuse
from handlers.coreLink import sitmap_get
from handlers.coreDatas import leancloud_push_userinfo
from handlers.coreDatas import leancloud_push


def main():
        # 引入leancloud验证
        if configs.DEBUG:
            leancloud.init(configs.LC_APPID, configs.LC_APPKEY)
            friendpage_link = configs.FRIENPAGE_LINK
        else:
            leancloud.init(sys.argv[1], sys.argv[2])
            friendpage_link = sys.argv[3]

        # 导入yml配置文件
        # config = load_config()
        config = configs.yml

        # 执行主方法
        print('----------------------')
        print('-----------！！开始执行爬取文章任务！！----------')
        print('----------------------')
        print('\n')
        # 分离到handlers.coreDatas.py
        # today = datetime.datetime.today()
        # time_limit = 60
        friend_poor = []
        post_poor = []
        print('----------------------')
        print('-----------！！开始执行友链获取任务！！----------')
        print('----------------------')
        if config['setting']['gitee_friends_links']['enable'] and config['setting']['gitee_friends_links']['type'] == 'normal':
            try:
                kang_api(friend_poor)
            except:
                print('读取gitee友链失败')
        else:
            print('未开启gitee友链获取')
        if config['setting']['github_friends_links']['enable'] and config['setting']['github_friends_links']['type'] == 'normal':
            try:
                github_issuse(friend_poor)
            except:
                print('读取github友链失败')
        else:
            print('未开启gihub友链获取')
        try:
            butterfly.butterfly_get_friendlink(friendpage_link,friend_poor)
        except:
            print('不是butterfly主题')
        try:
            matery.matery_get_friendlink(friendpage_link,friend_poor)
        except:
            print('不是matery主题')
        try:
            volantis.volantis_get_friendlink(friendpage_link,friend_poor)
        except:
            print('不是volantis主题或未配置gitee友链')
        friend_poor = delete_same_link(friend_poor)
        friend_poor = block_link(friend_poor)
        print('当前友链数量', len(friend_poor))
        print('----------------------')
        print('-----------！！结束友链获取任务！！----------')
        print('----------------------')
        total_count = 0
        error_count = 0
        for index, item in enumerate(friend_poor):
            error = 'false'
            try:
                total_count += 1
                error = butterfly.get_last_post_from_butterfly(item, post_poor)
                if error == 'true':
                    error = matery.get_last_post_from_matery(item, post_poor)
                if error == 'true':
                    error = volantis.get_last_post_from_volantis(item, post_poor)
                if error == 'true':
                    print("-----------获取主页信息失败，采取sitemap策略----------")
                    error, post_poor = sitmap_get(item, post_poor)
            except Exception as e:
                print('\n')
                print(item, "运用主页及sitemap爬虫爬取失败！请检查")
                print('\n')
                print(e)
                error_count += 1
            item.append(error)
        print('\n')
        print('----------------------')
        print("一共进行%s次" % total_count)
        print("一共失败%s次" % error_count)
        print('----------------------')
        print('\n')
        print('----------------------')
        print('-----------！！执行用户信息上传！！----------')
        print('----------------------')
        leancloud_push_userinfo(friend_poor)
        print('----------------------')
        print('-----------！！用户信息上传完毕！！----------')
        print('----------------------')
        post_poor.sort(key=itemgetter('time'), reverse=True)
        print('----------------------')
        print('-----------！！执行文章信息上传！！----------')
        print('----------------------')
        leancloud_push(post_poor)
        print('----------------------')
        print('-----------！！文章信息上传完毕！！----------')
        print('----------------------')

if __name__ == '__main__':
    main()
