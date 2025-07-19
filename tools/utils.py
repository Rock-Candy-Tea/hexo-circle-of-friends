# -*- coding:utf-8 -*-
# Author：yyyz
import yaml
import os
from tools import baselogger


def get_base_path():
    base_path = os.environ.get(
        "BASE_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
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
    path = os.path.join(base_path, "fc_settings.yaml")
    try:
        logger.debug("读取配置文件...")
        f = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        logger.critical("读取配置文件失败！请检查用户配置文件是否正确！")
        raise IOError
    try:
        user_conf = yaml.safe_load(f)
    except:
        logger.critical("读取配置文件失败，请检查配置文件内容语法是否正确！")
        raise IOError
    logger.debug("成功获取用户配置！")
    f.close()
    return user_conf


def is_vercel_sqlite():
    settings = get_user_settings()
    return os.environ.get("VERCEL") and settings["DATABASE"] == "sqlite"


def is_vercel():
    return os.environ.get("VERCEL")


if __name__ == "__main__":
    print(get_user_settings())
