# -*- coding:utf-8 -*-

import re

from scrapy.exceptions import DropItem
from ..utils import process_time


class DuplicatesPipeline:
    def __init__(self):
        self.data_link_set = set()  # 通过链接对post文章数据的去重
        self.data_title_set = set()  # 通过标题对post文章数据的去重
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
        title = item['title']
        if link in self.data_link_set or link == "":
            raise DropItem("Duplicate found:%s" % link)

        if title in self.data_title_set or title == "":
            raise DropItem("Duplicate found:%s" % title)

        if not re.match("^http.?://", item["link"]):
            # 链接必须是http开头，不能是相对地址
            raise DropItem("invalid link ")

        # 时间检查
        if not process_time.format_check(item["created"], item["updated"]):
            raise DropItem("invalid time ")

        if not process_time.content_check(item["created"], item["updated"]):
            raise DropItem("invalid time ")

        self.data_link_set.add(link)
        self.data_title_set.add(title)
        return item
