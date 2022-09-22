import contextlib
import os
import sys

from hexo_circle_of_friends import scrapy_conf, models
from hexo_circle_of_friends.utils.project import get_user_settings, get_base_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


class SQLEngine(object):
    engine = None

    def __new__(cls):
        if cls.engine is None:
            cls.engine = cls.__get_sql_engine()
            # 创建表
            models.Model.metadata.create_all(cls.engine)
        return cls.engine

    @staticmethod
    def __get_sql_engine():
        settings = get_user_settings()
        base_path = get_base_path()
        if scrapy_conf.DEBUG:
            if settings["DATABASE"] == "sqlite":
                if sys.platform == "win32":
                    conn = rf"sqlite:///{os.path.join(base_path, 'data.db')}"
                else:
                    conn = f"sqlite:////{os.path.join(base_path, 'data.db')}"
                # conn = "sqlite:///" + BASE_DIR + "/data.db" + "?check_same_thread=False"
            elif settings["DATABASE"] == "mysql":
                conn = "mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4" \
                       % ("root", "123456", "localhost", "test")
            else:
                raise
        else:
            if settings["DATABASE"] == "sqlite":
                if sys.platform == "win32":
                    conn = rf"sqlite:///{os.path.join(base_path, 'data.db')}"
                else:
                    conn = f"sqlite:////{os.path.join(base_path, 'data.db')}"
                # conn = "sqlite:///" + BASE_DIR + "/data.db" + "?check_same_thread=False"
            elif settings["DATABASE"] == "mysql":
                conn = "mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4" \
                       % (os.environ["MYSQL_USERNAME"], os.environ["MYSQL_PASSWORD"], os.environ["MYSQL_IP"]
                          , os.environ["MYSQL_PORT"], os.environ["MYSQL_DB"])
            else:
                raise
        try:
            engine = create_engine(conn, pool_recycle=-1)
        except:
            raise Exception("MySQL连接失败")
        return engine


def db_init():
    engine = SQLEngine()
    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)
    return session



