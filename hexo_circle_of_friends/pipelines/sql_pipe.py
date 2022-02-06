# -*- coding:utf-8 -*-
# Author：yyyz
import os
import datetime
import re

from .. import models,settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session

class SQLPipeline:
    def __init__(self):
        self.userdata = []
        self.nonerror_data = set()  # 能够根据友链link获取到文章的人

    def open_spider(self, spider):
        if settings.DEBUG:
            if settings.DATABASE == "sqlite":
                conn = "sqlite:///data.db"
            elif settings.DATABASE == "mysql":
                conn = "mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4"\
                       %("root", "123456", "localhost", "test")
        else:
            if settings.DATABASE == "sqlite":
                conn = "sqlite:///data.db"
            elif settings.DATABASE == "mysql":
                conn = "mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4"\
                       %(os.environ["MYSQL_USERNAME"], os.environ["MYSQL_PASSWORD"], os.environ["MYSQL_IP"], os.environ["MYSQL_DB"])
        try:
            self.engine = create_engine(conn,pool_recycle=-1)
        except:
            raise Exception("MySQL连接失败")
        Session = sessionmaker(bind=self.engine)
        self.session = scoped_session(Session)

        # 创建表
        models.Model.metadata.create_all(self.engine)
        # 删除friend表
        self.session.query(models.Friend).delete()
        # 获取post表数据
        self.query_post()
        print("Initialization complete")

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
            if item["name"] in self.nonerror_data:
                pass
            else:
                # 未失联的人
                self.nonerror_data.add(item["name"])

            # print(item)
            for query_item in self.query_post_list:
                try:
                    if query_item.link == item["link"]:
                        item["time"] = min(item['time'], query_item.created)
                        self.session.query(models.Post).filter_by(id=query_item.id).delete()
                        self.session.commit()
                        # print("----deleted %s ----"%item["title"])
                except:
                    pass

            self.friendpoor_push(item)

        return item

    def close_spider(self,spider):
        # print(self.nonerror_data)
        # print(self.userdata)

        self.friendlist_push()

        self.outdate_clean(settings.OUTDATE_CLEAN)
        print("----------------------")
        print("友链总数 : %d" %self.session.query(models.Friend).count())
        print("失联友链数 : %d" % self.session.query(models.Friend).filter_by(error=True).count())
        print("共 %d 篇文章"%self.session.query(models.Post).count())
        self.session.close()
        print("done!")

    def query_post(self):
        try:
            self.query_post_list = self.session.query(models.Post).all()
        except:
            self.query_post_list=[]

    def outdate_clean(self,time_limit):
        out_date_post = 0
        for query_item in self.query_post_list:
            created = query_item.created
            try:
                query_time = datetime.datetime.strptime(created, "%Y-%m-%d")
                if (datetime.datetime.today() - query_time).days > time_limit:
                    self.session.query(models.Post).filter_by(id=query_item.id).delete()
                    out_date_post += 1
                    self.session.commit()
            except:
                self.session.query(models.Post).filter_by(id=query_item.id).delete()
                self.session.commit()
                out_date_post += 1
        # print('\n')
        # print('共删除了%s篇文章' % out_date_post)
        # print('\n')
        # print('-------结束删除规则----------')

    def friendlist_push(self):
        for user in self.userdata:
            friend = models.Friend(
                name= user[0],
                link = user[1],
                avatar = user[2]
            )
            if user[0] in self.nonerror_data:
                # print("未失联的用户")
                friend.error = False
            elif settings.BLOCK_SITE:
                error = True
                for url in settings.BLOCK_SITE:
                    if re.match(url, friend.name):
                        friend.error = False
                if error:
                    print("请求失败，请检查链接： %s" % friend.link)
                    friend.error = True
            else:
                print("请求失败，请检查链接： %s" % friend.link)
                friend.error = True
            self.session.add(friend)
            self.session.commit()

    def friendpoor_push(self,item):
        post = models.Post(
            title=item['title'],
            created=item['time'],
            updated=item['updated'],
            link=item['link'],
            author=item['name'],
            avatar=item['img'],
            rule=item['rule']
        )
        self.session.add(post)
        self.session.commit()
        print("----------------------")
        print(item["name"])
        print("《{}》\n文章发布时间：{}\t\t采取的爬虫规则为：{}".format(item["title"], item["time"], item["rule"]))