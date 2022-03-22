# -*- coding:utf-8 -*-
# Author：yyyz
import os
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from settings import *
import schedule
from multiprocessing.context import Process
import time
import requests


def main():
    # 获取settings
    setting = get_project_settings()
    # init settings
    initsettings(setting)
    process = CrawlerProcess(setting)
    didntWorkSpider = ['xiaoso', ]
    for spider_name in process.spiders.list():
        if spider_name in didntWorkSpider:
            continue
        # print("Running spider %s" % (spider_name))
        process.crawl(spider_name)
    process.start()


def settings_friends_json_parse(setting):
    import json
    try:
        response = requests.get(setting["SETTINGS_FRIENDS_LINKS"]["json_api"])
        friends = json.loads(response.text)["friends"]
        setting["SETTINGS_FRIENDS_LINKS"]["list"].extend(friends)
    except:
        pass


def sub_process_start():
    process = Process(target=main)
    process.start()  # 开始执行
    process.join()  # 阻塞等待进程执行完毕


def initsettings(setting):
    # 根据所配置的数据库类型选择pipeline
    if DATABASE == 'leancloud':
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.leancloud_pipe.LeancloudPipeline"] = 300
    elif DATABASE == 'mysql' or DATABASE == "sqlite":
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.sql_pipe.SQLPipeline"] = 300
    elif DATABASE == "mongodb":
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.mongodb_pipe.MongoDBPipeline"] = 300
    # 如果配置了json_api友链，在这里进行获取
    if SETTINGS_FRIENDS_LINKS["json_api"].startswith("http"):
        settings_friends_json_parse(setting)


if __name__ == '__main__':
    if DEPLOY_TYPE == "docker" or DEPLOY_TYPE == "server":
        # server/docker部署
        # 根据环境变量获取运行间隔时间，默认6小时运行一次
        run_per_hours = int(os.environ["RUN_PER_HOURS"]) if os.environ.get("RUN_PER_HOURS") else 6
        schedule.every(run_per_hours).hours.do(sub_process_start)
        schedule.run_all()
        while 1:
            n = schedule.idle_seconds()
            if n is None:
                # no more jobs
                break
            elif n > 0:
                # sleep exactly the right amount of time
                time.sleep(n)
            schedule.run_pending()
    else:
        main()
