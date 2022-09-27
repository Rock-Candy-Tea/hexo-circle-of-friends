import os
from pymongo import MongoClient
from hexo_circle_of_friends import scrapy_conf


class MongoEngine(object):
    engine = None

    def __new__(cls):
        if cls.engine is None:
            cls.engine = cls.__get_mongo_engine()
        return cls.engine

    @staticmethod
    def __get_mongo_engine():
        if scrapy_conf.DEBUG:
            URI = "mongodb+srv://yyyz:etmTvVcvOGlSINSm@cluster0.c6dgw.mongodb.net/?retryWrites=true&w=majority"
        else:
            URI = os.environ.get("MONGODB_URI")
        client = MongoClient(URI)
        return client


def db_init():
    engine = MongoEngine()
    fcircle_session = engine.fcircle
    return fcircle_session
