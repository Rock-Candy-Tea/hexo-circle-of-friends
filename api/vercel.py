# -*- coding:utf-8 -*-
import sys
import os
import uvicorn

# 将项目根目录添加到Python的搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import baselogger
from tools.utils import get_user_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 日志记录配置
# baselogger.init_logging_conf()
# logger = baselogger.get_logger(__name__)

settings = get_user_settings()
if settings["DATABASE"] == "mysql" or settings["DATABASE"] == "sqlite":
    from api_dependence.sql.sqlapi import (
        query_all,
        query_friend,
        query_random_friend,
        query_random_post,
        query_post,
    )
elif settings["DATABASE"] == "mongodb":
    from api_dependence.mongodb.mongodbapi import (
        query_all,
        query_friend,
        query_random_friend,
        query_random_post,
        query_post,
    )
else:
    raise Exception("DATABASE not supported")

OUTDATE_CLEAN = settings["OUTDATE_CLEAN"]

app = FastAPI(docs_url=None, redoc_url=None)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/all", tags=["PUBLIC_API"], summary="返回完整统计信息")
def all(start: int = 0, end: int = -1, rule: str = "updated"):
    """返回数据库统计信息和文章信息列表
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间created/更新时间updated）
    """
    list_ = ["title", "created", "updated", "link", "author", "avatar"]
    return query_all(list_, start, end, rule)


@app.get("/friend", tags=["PUBLIC_API"], summary="返回所有友链")
def friend():
    """返回数据库友链列表"""
    return query_friend()


@app.get("/randomfriend", tags=["PUBLIC_API"], summary="返回随机友链")
def random_friend(num: int = 1):
    """
    随机返回num个友链信息：
    - num=1，返回友链信息的字典
    - num>1，返回包含num个友链信息字典的列表
    """
    return query_random_friend(num)


@app.get("/randompost", tags=["PUBLIC_API"], summary="返回随机文章")
def random_post(num: int = 1):
    """
    随机返回num篇文章信息：
    - num=1，返回文章信息的字典
    - num>1，返回包含num个文章信息字典的列表
    """
    return query_random_post(num)


@app.get("/post", tags=["PUBLIC_API"], summary="返回指定链接的所有文章")
def post(link: str | None = None, num: int = -1, rule: str = "created"):
    """返回指定链接的数据库内文章信息列表
    - link: 链接地址
    - num: 指定链接的文章信息列表 按rule排序后的顺序的前num篇
    - rule: 文章排序规则（创建时间/更新时间）
    """
    return query_post(link, num, rule)


if __name__ == "__main__":
    if settings["DEPLOY_TYPE"] == "docker":
        uvicorn.run("vercel:app", host="0.0.0.0")
    elif settings["DEPLOY_TYPE"] == "server":
        EXPOSE_PORT = (
            int(os.environ["EXPOSE_PORT"]) if os.environ.get("EXPOSE_PORT") else 8000
        )
        uvicorn.run("vercel:app", host="0.0.0.0", port=EXPOSE_PORT)
    else:
        uvicorn.run("vercel:app", host="0.0.0.0", reload=True)
