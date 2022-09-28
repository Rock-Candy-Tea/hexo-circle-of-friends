# -*- coding:utf-8 -*-
# Author：yyyz
import yaml
import os
from . import baselogger


def get_base_path():
    base_path = os.environ.get("BASE_PATH",
                               os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # assert base_path, "Environment variable 'BASE_PATH' is not detected," \
    #                   f"make sure it is added! {os.getcwd()},,{sys.argv[0]}"
    return base_path


def get_user_settings():
    """
    加载用户配置文件
    :return:
    """
    logger = baselogger.get_logger(__name__)
    base_path = get_base_path()
    path = os.path.join(base_path, "dump_settings.yaml")
    try:
        logger.debug("读取远程自动配置...")
        f = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        logger.debug("读取远程自动配置失败！")
        path = os.path.join(base_path, "hexo_circle_of_friends/fc_settings.yaml")
        try:
            logger.debug("读取本地手动配置...")
            f = open(path, "r", encoding="utf-8")
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
