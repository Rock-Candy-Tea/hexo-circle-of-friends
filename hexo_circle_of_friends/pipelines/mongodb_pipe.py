# -*- coding:utf-8 -*-
# Author：yyyz
import os
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
from ..utils import baselogger

today = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
logger = baselogger.get_logger(__name__)

class MongoDBPipeline:
    def __init__(self):
        self.userdata = []
        self.nonerror_data = set()  # 能够根据友链link获取到文章的人
        self.query_post_list = []

    def open_spider(self, spider):
        settings = spider.settings
        if settings["DEBUG"]:
            uri = "mongodb+srv://yyyz:etmTvVcvOGlSINSm@cluster0.c6dgw.mongodb.net/?retryWrites=true&w=majority"
        else:
            uri = os.environ.get("MONGODB_URI")
        client = MongoClient(uri)
        db = client.fcircle
        self.posts = db.Post
        self.friends = db.Friend
        self.query_post_num = self.posts.count_documents({})

        self.query_post()

        self.friends.delete_many({})
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
            for query_item in self.query_post_list[:self.query_post_num]:
                try:
                    if query_item["link"] == item["link"]:
                        query_item['created'] = min(item['created'], query_item.get("created"))
                        post_id = query_item.get("_id")
                        self.posts.delete_one({"_id": post_id})
                except:
                    post_id = query_item.get("_id")
                    self.posts.delete_one({"_id": post_id})

            self.friendpoor_push(item)

        return item

    def close_spider(self, spider):
        # print(self.nonerror_data)
        # print(self.userdata)
        settings = spider.settings
        count, error_num = self.friendlist_push(settings)
        self.outdate_clean(settings["OUTDATE_CLEAN"])
        logger.info("----------------------")
        logger.info("友链总数 : %d" % count)
        logger.info("失联友链数 : %d" % error_num)
        logger.info("共 %d 篇文章" % self.posts.count_documents({}))
        logger.info("最后运行于：%s" % today)
        logger.info("done!")

    def query_post(self):
        try:
            self.query_post_list = []
            for post in self.posts.find():
                self.query_post_list.append(post)
        except:
            self.query_post_list = []

    def outdate_clean(self, time_limit):
        out_date_post = 0
        self.query_post()
        for query_item in self.query_post_list:
            updated = query_item.get("updated")
            try:
                query_time = datetime.strptime(updated, "%Y-%m-%d")
                if (datetime.utcnow() + timedelta(hours=8) - query_time).days > time_limit:
                    result = self.posts.delete_one({"_id": query_item.get("_id")})
                    out_date_post += 1
            except:
                self.posts.delete_one({"_id": query_item.get("_id")})
                out_date_post += 1
        # print('\n')
        # print('共删除了%s篇文章' % out_date_post)
        # print('\n')
        # print('-------结束删除规则----------')

    def friendlist_push(self, settings):
        friends = []
        error_num = 0
        for user in self.userdata:
            friend = {
                "name": user[0],
                "link": user[1],
                "avatar": user[2],
                "createdAt": today,
            }
            if user[0] in self.nonerror_data:
                # print("未失联的用户")
                friend["error"] = False
            elif settings["BLOCK_SITE"]:
                error = True
                for url in settings["BLOCK_SITE"]:
                    if re.match(url, friend["link"]):
                        friend["error"] = False
                        error = False
                if error:
                    logger.error("请求失败，请检查链接： %s" % friend["link"])
                    friend["error"] = True
                    error_num += 1
            else:
                logger.error("请求失败，请检查链接： %s" % friend["link"])
                friend["error"] = True
                error_num += 1
            friends.append(friend)

        for friend in friends:
            try:
                self.friends.replace_one({"link": friend.get("link")}, friend, upsert=True)
            except:
                logger.error("上传数据失败，请检查：%s" % friend.get("link"))
        return len(friends), error_num

    def friendpoor_push(self, item):
        item["createdAt"] = today
        try:
            self.posts.replace_one({"link": item.get("link")}, item, upsert=True)
        except:
            pass

        info = f"""\033[1;34m\n——————————————————————————————————————————————————————————————————————————————
{item['author']}\n《{item['title']}》\n文章发布时间：{item['created']}\t\t采取的爬虫规则为：{item['rule']}
——————————————————————————————————————————————————————————————————————————————\033[0m"""
        logger.info(info)
