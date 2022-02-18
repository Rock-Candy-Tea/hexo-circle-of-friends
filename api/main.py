# -*- coding:utf-8 -*-
import asyncio
import re
import aiohttp
from lxml import etree
import uvicorn
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from hexo_circle_of_friends import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if settings.DATABASE == 'leancloud':
    from api.leancloudapi import *
elif settings.DATABASE == "mysql" or settings.DATABASE == "sqlite":
    from api.sqlapi import *
elif settings.DATABASE == "mongodb":
    from api.mongodbapi import *

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
def all(start: int = 0, end: int = -1, rule: str = "updated"):
    '''返回数据库统计信息和文章信息列表
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间/更新时间）
    '''
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_all(list, start, end, rule)


@app.get("/friend", tags=["API"], summary="返回所有友链")
def friend():
    '''返回数据库友链列表
    '''
    return query_friend()


@app.get("/randomfriend", tags=["API"], summary="返回随机友链")
def random_friend():
    '''随机返回一个友链信息
    '''
    return query_random_friend()


@app.get("/randompost", tags=["API"], summary="返回随机文章")
def random_post():
    '''随机返回一篇文章信息
    '''
    return query_random_post()


@app.get("/post", tags=["API"], summary="返回指定链接的所有文章")
def post(link: str = None, num: int = -1, rule: str = "created"):
    '''返回指定链接的数据库内文章信息列表
    - link: 链接地址
    - num: 指定链接的文章信息列表 按rule排序后的顺序的前num篇
    - rule: 文章排序规则（创建时间/更新时间）
    '''
    return query_post(link, num, rule)


@app.get("/postjson", tags=["API"], summary="返回指定所有链接的所有文章")
def postjson(jsonlink: str, start: int = 0, end: int = -1, rule: str = "updated"):
    '''获取公共库中指定链接列表的文章信息列表
    - jsonlink: 友链链接json的cdn地址
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间/更新时间）
    '''
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_post_json(jsonlink, list, start, end, rule)


@app.get("/version", tags=["version"], summary="返回版本信息")
async def version():
    # status:0 不需要更新；status:1 需要更新 status:2 检查更新失败
    api_json = {"status": 0}
    if settings.VERSION:
        try:
            async with aiohttp.ClientSession() as session:
                urls = [
                    "https://hexo-circle-of-friends-doc.vercel.app/version.txt",
                    "https://hiltay.github.io/hexo-circle-of-friends-doc/version.txt",
                    "https://github.com/Rock-Candy-Tea/hexo-circle-of-friends"
                ]
                tasks = [asyncio.create_task(fetch(session, url)) for url in urls]
                done, pending = await asyncio.wait(tasks)
                for d in done:
                    if d.result():
                        api_json["current_version"] = settings.VERSION
                        api_json["latest_version"] = d.result()
        except:
            api_json["current_version"] = settings.VERSION
            api_json["status"] = 2
            return api_json
        if settings.VERSION != api_json["latest_version"]:
            api_json["status"] = 1
        return api_json


async def fetch(session, url):
    async with session.get(url, verify_ssl=False) as response:
        content = await response.text()
        if re.match("^\d+", content):
            return content
        else:
            html = etree.HTML(content)
            content = str(html.xpath("//body//div[@class='BorderGrid-cell']//div[@class='d-flex']/span/text()")[0])
            return content


if __name__ == "__main__":
    if settings.DEPLOY_TYPE == "docker":
        uvicorn.run("main:app", host="0.0.0.0")
    elif settings.DEPLOY_TYPE == "server":
        EXPOSE_PORT = int(os.environ["EXPOSE_PORT"]) if os.environ["EXPOSE_PORT"] else 8000
        uvicorn.run("main:app", host="0.0.0.0", port=EXPOSE_PORT)
    else:
        uvicorn.run("main:app", host="127.0.0.1")
