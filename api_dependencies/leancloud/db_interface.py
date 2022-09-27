import os
import leancloud
from hexo_circle_of_friends import scrapy_conf


def db_init():
    if scrapy_conf.DEBUG:
        leancloud.init(scrapy_conf.LC_APPID, scrapy_conf.LC_APPKEY)
    else:
        leancloud.init(os.environ["APPID"], os.environ["APPKEY"])
