# -*- coding:utf-8 -*-
# Author：yyyz
import os
import time
import requests
import schedule
from hexo_circle_of_friends.utils import baselogger, project
from multiprocessing.context import Process
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

# 日志记录配置
baselogger.init_logging_conf()
logger = baselogger.get_logger(__name__)


def main():
    # 读取用户配置
    user_conf = project.get_user_settings()
    # 获取settings
    settings = get_project_settings()
    # 初始化settings
    initsettings(settings, user_conf)
    process = CrawlerProcess(settings)
    didntWorkSpider = []
    for spider_name in process.spider_loader.list():
        if spider_name in didntWorkSpider:
            continue
        # print("Running spider %s" % (spider_name))
        process.crawl(spider_name)
    process.start()


def settings_friends_json_parse(json_file, user_conf):
    """
    json格式友链解析，并配置到setting中
    :param json_file: 友链字典
    :param user_conf: 配置
    :return:
    """
    if not json_file.get("friends"):
        logger.warning(f"json_api格式错误：没有friends字段")
        return
    friends = json_file["friends"]
    # 数据形式：0：未知；1：普通格式；2：进阶格式
    data_type = 0
    try:
        if isinstance(friends[0], list):
            data_type = 1
        elif isinstance(friends[0], dict):
            data_type = 2
    except:
        logger.warning(f"json_api格式错误：无法判定数据形式")

    if data_type == 1:
        # 普通格式
        user_conf["SETTINGS_FRIENDS_LINKS"]["list"].extend(friends)
    elif data_type == 2:
        # 进阶格式
        try:
            for dic in json_file["friends"]:
                link_list = dic["link_list"]
                for link in link_list:
                    # 必须有name、link、avatar字段
                    name = link.get("name")
                    friendlink = link.get("link")
                    avatar = link.get("avatar")
                    suffix = link.get("suffix")
                    if name and friendlink and avatar:
                        friends = [name, friendlink, avatar]
                        if suffix:
                            friends.append(suffix)
                        user_conf["SETTINGS_FRIENDS_LINKS"]["list"].append(friends)
        except:
            logger.warning(f"json_api进阶格式解析错误")
    else:
        logger.warning(f"json_api格式错误：无法判定数据形式")


def settings_friends_json_read(json_api, user_conf):
    """
    判断配置方式，读取json文件
    :param json_api: api地址
    :param user_conf: 配置
    :return:
    """
    import json
    # 解析json友链
    if json_api.startswith("http"):
        # 通过url配置的在线json，发送请求获取
        try:
            response = requests.get(user_conf["SETTINGS_FRIENDS_LINKS"]["json_api"])
            file = json.loads(response.text)
            settings_friends_json_parse(file, user_conf)
        except:
            logger.warning(f"在线解析：{json_api} 失败")
    elif os.path.isfile(json_api) and json_api.endswith(".json"):
        # 如果是json文件的形式配置，直接读取
        try:
            with open(json_api, "r", encoding="utf-8") as f:
                file = json.load(f)
                settings_friends_json_parse(file, user_conf)
        except:
            logger.warning(f"加载文件：{json_api} 失败")


def sub_process_start():
    process = Process(target=main)
    process.start()  # 开始执行
    process.join()  # 阻塞等待进程执行完毕


def initsettings(settings, user_conf):
    db = user_conf["DATABASE"]
    # 根据所配置的数据库类型选择pipeline
    if db == 'leancloud':
        settings["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.leancloud_pipe.LeancloudPipeline"] = 300
    elif db == 'mysql' or db == "sqlite":
        settings["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.sql_pipe.SQLPipeline"] = 300
    elif db == "mongodb":
        settings["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.mongodb_pipe.MongoDBPipeline"] = 300

    setting_friends = user_conf["SETTINGS_FRIENDS_LINKS"]
    # 如果配置了json_api友链，在这里进行获取
    if setting_friends["enable"] and setting_friends["json_api"]:
        json_api = setting_friends["json_api"]
        settings_friends_json_read(json_api, user_conf)
    # 添加用户配置
    for k, v in user_conf.items():
        settings.set(k, v)


if __name__ == '__main__':
    conf = project.get_user_settings()
    DEPLOY_TYPE = conf["DEPLOY_TYPE"]
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
