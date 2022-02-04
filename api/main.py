# -*- coding:utf-8 -*-
import uvicorn
from hexo_circle_of_friends import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if settings.DATABASE == 'leancloud':
    from leancloudapi import *
elif settings.DATABASE == "mysql" or settings.DATABASE == "sqlite":
    from sqlapi import *

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/all", tags=["API"], summary="返回完整统计信息")
async def all(start: int = 0, end: int = -1, rule: str = "created"):
    '''返回数据库统计信息和文章信息列表
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间/更新时间）
    '''
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_all(list, start, end, rule)


@app.get("/friend", tags=["API"], summary="返回所有友链")
async def friend():
    '''返回数据库友链列表
    '''
    return query_friend()


@app.get("/randomfriend", tags=["API"], summary="返回随机友链")
async def random_friend():
    '''随机返回一个友链信息
    '''
    list = ['name', 'link', 'avatar']
    return query_random_friend(list)


@app.get("/randompost", tags=["API"], summary="返回随机文章")
async def random_post():
    '''随机返回一篇文章信息
    '''
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_random_post(list)


@app.get("/post", tags=["API"], summary="返回指定链接的所有文章")
async def post(link: str = None, num: int = -1, rule: str = "created"):
    '''返回指定链接的数据库内文章信息列表
    - link: 链接地址
    - num: 指定链接的文章信息列表 按rule排序后的顺序的前num篇
    - rule: 文章排序规则（创建时间/更新时间）
    '''
    list = ['title', 'link', 'created', 'updated']
    return query_post(link, num, rule, list)


@app.get("/postjson", tags=["API"], summary="返回指定所有链接的所有文章")
async def postjson(jsonlink: str, start: int = 0, end: int = -1, rule: str = "updated"):
    '''获取公共库中指定链接列表的文章信息列表
    - jsonlink: 友链链接json的cdn地址
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间/更新时间）
    '''
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_post_json(jsonlink, list, start, end, rule)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1")