# -*- coding:utf-8 -*-
# Author：yyyz
import yaml
import traceback
from . import baselogger
import os

os.environ["BASE_PATH"] = "/root/data/"


def get_user_settings():
    """
    加载用户配置文件
    :return:
    """
    logger = baselogger.get_logger(__name__)
    base_path = os.environ.get("BASE_PATH", "")
    path = os.path.join(base_path, "hexo_circle_of_friends/dump_settings")
    try:
        logger.debug("读取远程自动配置...")
        f = open(path, "r")
    except FileNotFoundError:
        logger.debug("读取远程自动配置失败！")
        path = os.path.join(base_path, "hexo_circle_of_friends/fc_settings.yaml")
        try:
            logger.debug("读取本地手动配置...")
            f = open(path, "r")
        except:
            logger.critical("读取本地手动配置失败！请检查用户配置文件是否正确！")
            raise IOError
    try:
        user_conf = yaml.safe_load(f)
    except:
        logger.critical("读取本地手动配置失败，请检查配置文件内容语法是否正确！")
        raise IOError
    logger.debug("成功获取用户配置！")
    f.close()
    return user_conf


