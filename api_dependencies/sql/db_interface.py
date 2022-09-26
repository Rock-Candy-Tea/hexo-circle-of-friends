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
        db_path = os.path.join(base_path, 'data.db')
        if scrapy_conf.DEBUG:
            if settings["DATABASE"] == "sqlite":
                if sys.platform == "win32":
                    conn = rf"sqlite:///{db_path}?check_same_thread=False"
                else:
                    conn = f"sqlite:////{db_path}?check_same_thread=False"
                # conn = "sqlite:///" + BASE_DIR + "/data.db" + "?check_same_thread=False"
            elif settings["DATABASE"] == "mysql":
                conn = "mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4" \
                       % ("root", "123456", "localhost", "test")
            else:
                raise
        else:
            if settings["DATABASE"] == "sqlite":
                if sys.platform == "win32":
                    conn = rf"sqlite:///{db_path}?check_same_thread=False"
                elif os.environ.get("VERCEL"):
                    # vercel production environment is a read-only file system
                    # see: https://github.com/vercel/community/discussions/314?sort=new
                    # here are temporary storage solution: copy base_path/data.db to /tmp/data.db
                    # Most containers have a /tmp folder. It's a UNIX convention.
                    # Usually held in memory and cleared on reboot. Don't need to create the folder yourself.
                    with open(db_path, "rb") as f:
                        binary_content = f.read()
                    with open("/tmp/data.db", "wb") as f:
                        f.write(binary_content)
                    conn = f"sqlite:////tmp/data.db?check_same_thread=False"
                else:
                    conn = f"sqlite:////{db_path}?check_same_thread=False"
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


def create_all_table():
    engine = SQLEngine()
    models.Model.metadata.create_all(engine)


def db_init():
    engine = SQLEngine()
    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)
    return session
