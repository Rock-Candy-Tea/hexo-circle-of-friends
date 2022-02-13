# -*- coding:utf-8 -*-

import re

from scrapy.exceptions import DropItem
from ..utils import process_time


class DuplicatesPipeline:
    def __init__(self):
        self.data_set = set()  # posts filter set 用于对post文章数据的去重
        self.friends_set = set()  # friends filter set 用于对friends的去重

    def process_item(self, item, spider):
        if "userdata" in item.keys():
            #  userdata filter
            link = item["link"]
            if link in self.friends_set:
                raise DropItem("Duplicate found:%s" % link)
            self.friends_set.add(link)
            return item

        link = item['link']
        if link in self.data_set or link == "":
            # 重复数据清洗
            raise DropItem("Duplicate found:%s" % link)
        if not item["title"]:
            raise DropItem("missing fields :'title'")
        elif not re.match("^http.?://", item["link"]):
            # 链接必须是http开头，不能是相对地址
            raise DropItem("invalid link ")

        # 时间检查
        if not process_time.format_check(item["created"], item["updated"]):
            raise DropItem("invalid time ")

        if not process_time.content_check(item["created"], item["updated"]):
            raise DropItem("invalid time ")

        self.data_set.add(link)
        return item
