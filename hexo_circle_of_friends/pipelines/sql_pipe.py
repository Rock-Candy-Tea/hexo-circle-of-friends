# -*- coding:utf-8 -*-
# Author：yyyz
import os
import re
import sys
from urllib import parse
from .. import models
from ..utils import baselogger, project
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta

today = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
logger = baselogger.get_logger(__name__)


class SQLPipeline:
    def __init__(self):
        self.userdata = []
        self.nonerror_data = set()  # 能够根据友链link获取到文章的人

    def open_spider(self, spider):
        settings = spider.settings
        base_path = project.get_base_path()
        db = settings["DATABASE"]
        if settings["DEBUG"]:
            if db == "sqlite":
                if sys.platform == "win32":
                    conn = rf"sqlite:///{os.path.join(base_path, 'data.db')}?check_same_thread=False"
                else:
                    conn = f"sqlite:////{os.path.join(base_path, 'data.db')}?check_same_thread=False"
            elif db == "mysql":
                conn = "mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4" \
                       % ("root", "123456", "localhost", "test")
            else:
                raise Exception("SQL连接失败，不支持的数据库！")
        else:
            if db == "sqlite":
                conn = f"sqlite:////{os.path.join(base_path, 'data.db')}?check_same_thread=False"
            elif db == "mysql":
                conn = f"mysql+pymysql://{os.environ['MYSQL_USERNAME']}:{parse.quote_plus(os.environ['MYSQL_PASSWORD'])}" \
                       f"@{os.environ['MYSQL_IP']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DB']}?charset=utf8mb4"
            else:
                raise Exception("SQL连接失败，不支持的数据库！")
        try:
            self.engine = create_engine(conn, pool_recycle=-1)
        except:
            raise Exception("SQL连接失败")
        Session = sessionmaker(bind=self.engine)
        self.session = scoped_session(Session)

        # 创建表
        models.Model.metadata.create_all(self.engine)
        # 删除friend表
        self.session.query(models.Friend).delete()
        # 获取post表数据
        self.query_post()
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
                    if query_item.link == item["link"]:
                        item["created"] = min(item['created'], query_item.created)
                        self.session.query(models.Post).filter_by(link=query_item.link).delete()
                except:
                    pass

            self.friendpoor_push(item)

        return item

    def close_spider(self, spider):
        # print(self.nonerror_data)
        # print(self.userdata)
        settings = spider.settings
        self.friendlist_push(settings)
        self.outdate_clean(settings["OUTDATE_CLEAN"])
        logger.info("----------------------")
        logger.info("友链总数 : %d" % self.session.query(models.Friend).count())
        logger.info("失联友链数 : %d" % self.session.query(models.Friend).filter_by(error=True).count())
        logger.info("共 %d 篇文章" % self.session.query(models.Post).count())

        logger.info("最后运行于：%s" % today)
        logger.info("done!")

    def query_post(self):
        try:
            self.query_post_list = self.session.query(models.Post).all()
        except:
            self.query_post_list = []

    def outdate_clean(self, time_limit):
        out_date_post = 0
        self.query_post()
        for query_item in self.query_post_list:
            updated = query_item.updated
            try:
                query_time = datetime.strptime(updated, "%Y-%m-%d")
                if (datetime.utcnow() + timedelta(hours=8) - query_time).days > time_limit:
                    self.session.query(models.Post).filter_by(link=query_item.link).delete()
                    out_date_post += 1
            except:
                self.session.query(models.Post).filter_by(link=query_item.link).delete()
                out_date_post += 1
        self.session.commit()
        self.session.close()
        # print('\n')
        # print('共删除了%s篇文章' % out_date_post)
        # print('\n')
        # print('-------结束删除规则----------')

    def friendlist_push(self, settings):
        for user in self.userdata:
            friend = models.Friend(
                name=user[0],
                link=user[1],
                avatar=user[2]
            )
            if user[0] in self.nonerror_data:
                # print("未失联的用户")
                friend.error = False
            elif settings["BLOCK_SITE"]:
                error = True
                for url in settings["BLOCK_SITE"]:
                    if re.match(url, friend.link):
                        friend.error = False
                        error = False
                if error:
                    logger.error("请求失败，请检查链接： %s" % friend.link)
                    friend.error = True
            else:
                logger.error("请求失败，请检查链接： %s" % friend.link)
                friend.error = True
            self.session.add(friend)
            self.session.commit()

    def friendpoor_push(self, item):
        post = models.Post(
            title=item['title'],
            created=item['created'],
            updated=item['updated'],
            link=item['link'],
            author=item['author'],
            avatar=item['avatar'],
            rule=item['rule']
        )
        self.session.add(post)
        self.session.commit()

        info = f"""\033[1;34m\n——————————————————————————————————————————————————————————————————————————————
{item['author']}\n《{item['title']}》\n文章发布时间：{item['created']}\t\t采取的爬虫规则为：{item['rule']}
——————————————————————————————————————————————————————————————————————————————\033[0m"""
        logger.info(info)
