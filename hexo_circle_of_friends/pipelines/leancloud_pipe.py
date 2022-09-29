# -*- coding:utf-8 -*-
# Author：yyyz
import os
import leancloud
import re
from datetime import datetime, timedelta
from ..utils import baselogger

today = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
logger = baselogger.get_logger(__name__)


class LeancloudPipeline:
    def __init__(self):
        self.userdata = []
        self.nonerror_data = set()  # 能够根据友链link获取到文章的人
        self.total_post_num = 0
        self.total_friend_num = 0
        self.err_friend_num = 0

    def open_spider(self, spider):
        settings = spider.settings
        if settings["DEBUG"]:
            leancloud.init(settings["LC_APPID"], settings["LC_APPKEY"])
        else:
            leancloud.init(os.environ["APPID"], os.environ["APPKEY"])
        self.Friendslist = leancloud.Object.extend('friend_list')
        self.Friendspoor = leancloud.Object.extend('friend_poor')
        self.query_friendslist()

        for query_j in self.query_friend_list:
            delete = self.Friendslist.create_without_data(query_j.get('objectId'))
            delete.destroy()
        self.query_friendslist()
        self.query_friendspoor()

        # print(self.query_post_list)
        # print(self.query_friend_list)

        logger.info("Initialization complete")

    def process_item(self, item, spider):
        if "userdata" in item.keys():
            li = []
            li.append(item["name"])
            li.append(item["link"])
            li.append(item["img"])
            self.userdata.append(li)
            # print(item)
            return item

        if "title" in item.keys():
            if item["author"] in self.nonerror_data:
                pass
            else:
                # 未失联的人
                self.nonerror_data.add(item["author"])

            # print(item)
            for query_item in self.query_post_list:
                try:
                    if query_item.get("link") == item["link"]:
                        item["created"] = min(item['created'], query_item.get('created'))
                        delete = self.Friendspoor.create_without_data(query_item.get('objectId'))
                        delete.destroy()
                        # print("----deleted %s ----"%item["title"])
                except:
                    pass

            self.friendpoor_push(item)

        return item

    def close_spider(self, spider):
        # print(self.nonerror_data)
        # print(self.userdata)
        settings = spider.settings
        self.friendlist_push(settings)
        # 查询此时的所有文章
        self.query_friendspoor()
        # 过期文章清除
        self.outdate_clean(settings["OUTDATE_CLEAN"])
        logger.info("----------------------")
        logger.info("友链总数 : %d" % self.total_friend_num)
        logger.info("失联友链数 : %d" % self.err_friend_num)
        logger.info("共 %d 篇文章" % self.total_post_num)
        logger.info("最后运行于：%s" % today)
        logger.info("done!")

    def query_friendspoor(self):
        try:
            query = self.Friendspoor.query
            query.select("title", 'created', 'link', 'updated')
            query.limit(1000)
            self.query_post_list = query.find()
            # print(self.query_post_list)
        except:
            self.query_post_list = []

    def query_friendslist(self):
        try:
            query = self.Friendslist.query
            query.select('frindname', 'friendlink', 'firendimg', 'error')
            query.limit(1000)
            self.query_friend_list = query.find()
        except:
            self.query_friend_list = []

    def outdate_clean(self, time_limit):
        out_date_post = 0
        for query_i in self.query_post_list:

            updated = query_i.get('updated')
            try:
                query_time = datetime.strptime(updated, "%Y-%m-%d")
                if (datetime.utcnow() + timedelta(hours=8) - query_time).days > time_limit:
                    delete = self.Friendspoor.create_without_data(query_i.get('objectId'))
                    out_date_post += 1
                    delete.destroy()
            except:
                delete = self.Friendspoor.create_without_data(query_i.get('objectId'))
                delete.destroy()
                out_date_post += 1
        # print('\n')
        # print('共删除了%s篇文章' % out_date_post)
        # print('\n')
        # print('-------结束删除规则----------')

    def friendlist_push(self, settings):
        for index, item in enumerate(self.userdata):
            friendlist = self.Friendslist()
            friendlist.set('friendname', item[0])
            friendlist.set('friendlink', item[1])
            friendlist.set('firendimg', item[2])
            if item[0] in self.nonerror_data:
                # print("未失联的用户")
                friendlist.set('error', "false")
            elif settings["BLOCK_SITE"]:
                error = True
                for url in settings["BLOCK_SITE"]:
                    if re.match(url, item[1]):
                        friendlist.set('error', "false")
                        error = False
                if error:
                    self.err_friend_num += 1
                    logger.error("请求失败，请检查链接： %s" % item[1])
                    friendlist.set('error', "true")
            else:
                self.err_friend_num += 1
                logger.error("请求失败，请检查链接： %s" % item[1])
                friendlist.set('error', "true")
            friendlist.save()
            self.total_friend_num += 1

    def friendpoor_push(self, item):
        friendpoor = self.Friendspoor()
        friendpoor.set('title', item['title'])
        friendpoor.set('created', item['created'])
        friendpoor.set('updated', item['updated'])
        friendpoor.set('link', item['link'])
        friendpoor.set('author', item['author'])
        friendpoor.set('avatar', item['avatar'])
        friendpoor.set('rule', item['rule'])
        friendpoor.save()

        info = f"""\033[1;34m\n——————————————————————————————————————————————————————————————————————————————
{item['author']}\n《{item['title']}》\n文章发布时间：{item['created']}\t\t采取的爬虫规则为：{item['rule']}
——————————————————————————————————————————————————————————————————————————————\033[0m"""
        logger.info(info)
        self.total_post_num += 1
