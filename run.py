'''
!/usr/bin/env python3
-*- coding: utf-8 -*-
Github    : https://github.com/Rock-Candy-Tea
team      : Rock-Candy-Tea
vindicator: 
 - Zour     : https://github.com/Zfour
 - RaXianch : https://github.com/DeSireFire
 - noionion : https://github.com/2X-ercha

主程序

业务流程：
主程序-->（处理器handlers）控件—->组件(component)

组件作为最底层，单向调用。
处理器可以调用组件，组件不可以反向调用处理器或主程序里的代码块。
避免产生双向调用，执行流程不清。

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

'''

from operator import itemgetter
import leancloud
import sys

# component
from theme import butterfly,matery,volantis,sakura,fluid

# handlers
from handlers.coreSettings import configs
from handlers.coreLink import delete_same_link
from handlers.coreLink import block_link
from handlers.coreLink import kang_api
from handlers.coreLink import github_issuse
from handlers.coreLink import sitmap_get
from handlers.coreDatas import leancloud_push_userinfo
from handlers.coreDatas import leancloud_push

# threads
from queue import Queue
from threading import Thread

# ---------- #



# theme fit massage
themes = [
    butterfly,
    matery,
    volantis,
    sakura,
    fluid
]

# ---------- #

# get friendpage_link
def verification():
    # 引入leancloud验证
    if configs.DEBUG:
        leancloud.init(configs.LC_APPID, configs.LC_APPKEY)
        friendpage_link = configs.FRIENPAGE_LINK
    else:
        leancloud.init(sys.argv[1], sys.argv[2])
        friendpage_link = sys.argv[3]
    return friendpage_link

# get friend_link
def get_link(friendpage_link, config):
    friend_poor = []

    #　get gitee_issue
    # if config['setting']['gitee_friends_links']['enable'] and config['setting']['gitee_friends_links']['type'] == 'normal':
    if configs.gitee_friends_links['enable'] and configs.gitee_friends_links['type'] == 'normal':
        try:
            kang_api(friend_poor, config)
        except:
            print('读取gitee友链失败')
    else:
        print('未开启gitee友链获取')
    
    # get github_issue
    # if config['setting']['github_friends_links']['enable'] and config['setting']['github_friends_links']['type'] == 'normal':
    if configs.github_friends_links['enable'] and configs.github_friends_links['type'] == 'normal':
        try:
            github_issuse(friend_poor, config)
        except:
            print('读取github友链失败')

    # get theme_link
    for themelinkfun in themes:
        try:
            themelinkfun.get_friendlink(friendpage_link, friend_poor)
        except:
            pass
    friend_poor = delete_same_link(friend_poor)
    friend_poor = block_link(friend_poor)

    print('当前友链数量', len(friend_poor))
    return friend_poor

# get each_link_last_post
def get_post(friend_poor):
    total_count = 0
    error_count = 0
    post_poor = []

    def spider(item):
        nonlocal total_count
        nonlocal post_poor
        nonlocal error_count
        error = True
        try:
            total_count += 1
            if error:
                for themelinkfun in themes:
                    if not error:
                        break
                    error = themelinkfun.get_last_post(item, post_poor)
            if error: 
                print("-----------获取主页信息失败，采取sitemap策略----------")
                error, post_poor = sitmap_get(item, post_poor)
                
        except Exception as e:
            print('\n')
            print(item, "运用主页及sitemap爬虫爬取失败！请检查")
            print('\n')
            print(e)
            error_count += 1
        
        if error: error = 'true'
        else: error = 'false'
        item.append(error)
        return item

    # multithread process
    # ---------- #
    Q = Queue()

    for i in range(len(friend_poor)):
        Q.put(i)

    def multitask():
        while not Q.empty():
            i= Q.get()
            item = friend_poor[i]
            item = spider(item)

    cores = 128
    threads = []
    for _ in range(cores):
        t = Thread(target=multitask)
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # ---------- #
    
    print('\n----------------------\n一共进行{}次\n一共失败{}次\n----------------------\n'.format(total_count, error_count))
    return post_poor

def main():
    config = configs.yml

    friendpage_link = verification()

    print('----------------------\n-----------！！开始执行爬取文章任务！！----------\n----------------------\n')
    print('----------------------\n-----------！！开始执行友链获取任务！！----------\n----------------------\n')

    friend_poor = get_link(friendpage_link, config)

    print('----------------------\n-------------！！结束友链获取任务！！------------\n----------------------\n')
    print('----------------------\n---------！！开始执行最新文章获取任务！！--------\n----------------------\n')

    post_poor = get_post(friend_poor)

    print('----------------------\n-----------！！结束最新文章获取任务！！----------\n----------------------\n')
    print('----------------------\n-----------！！执行用户信息上传任务！！----------\n----------------------\n')

    leancloud_push_userinfo(friend_poor)
    
    print('----------------------\n-----------！！结束用户信息上传任务！！----------\n----------------------\n')
    
    post_poor.sort(key=itemgetter('time'), reverse=True)

    print('----------------------\n-----------！！执行文章信息上传任务！！----------\n----------------------\n')
    
    leancloud_push(post_poor)

    print('----------------------\n-----------！！结束文章信息上传任务！！----------\n----------------------\n')

# ---------- #

if __name__ == '__main__':
    main()