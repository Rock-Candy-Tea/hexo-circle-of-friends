# -*- coding:utf-8 -*-
import asyncio
import re
import aiohttp
from lxml import etree
import uvicorn
import os
import json
import sys
import yaml

# todo 爬虫正在运行时无法修改配置！
from hexo_circle_of_friends.utils.project import get_user_settings, get_base_path
from hexo_circle_of_friends import scrapy_conf
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api_dependencies.items import PassWord, FcEnv, FcSettings as item_fc_settings
from api_dependencies.utils.github_upload import create_or_update_file, get_b64encoded_data
from api_dependencies import format_response, tools

settings = get_user_settings()
if settings["DATABASE"] == 'leancloud':
    from api_dependencies.leancloud.leancloudapi import *
elif settings["DATABASE"] == "mysql" or settings["DATABASE"] == "sqlite":
    from api_dependencies.sql.sqlapi import *
elif settings["DATABASE"] == "mongodb":
    from api_dependencies.mongodb.mongodbapi import *

OUTDATE_CLEAN = settings["OUTDATE_CLEAN"]

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


@app.get("/all", tags=["PUBLIC_API"], summary="返回完整统计信息")
def all(start: int = 0, end: int = -1, rule: str = "updated"):
    """返回数据库统计信息和文章信息列表
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间/更新时间）
    """
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_all(list, start, end, rule)


@app.get("/friend", tags=["PUBLIC_API"], summary="返回所有友链")
def friend():
    """返回数据库友链列表
    """
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
def post(link: str = None, num: int = -1, rule: str = "created"):
    """返回指定链接的数据库内文章信息列表
    - link: 链接地址
    - num: 指定链接的文章信息列表 按rule排序后的顺序的前num篇
    - rule: 文章排序规则（创建时间/更新时间）
    """
    return query_post(link, num, rule)


@app.get("/friendstatus", tags=["PUBLIC_API"], summary="按照指定时间划分失联/未失联的友链信息")
def friend_status(days: int = OUTDATE_CLEAN):
    """按照指定时间划分失联/未失联的友链信息，默认距离今天2个月以上（60天以上）判定为失联友链
    days: 默认为60天，取自配置文件settings.py中的OUTDATE_CLEAN
    """
    return query_friend_status(days)


@app.get("/postjson", tags=["PUBLIC_API"], summary="返回指定所有链接的所有文章")
def postjson(jsonlink: str, start: int = 0, end: int = -1, rule: str = "updated"):
    """获取公共库中指定链接列表的文章信息列表
    - jsonlink: 友链链接json的cdn地址
    - start: 文章信息列表从 按rule排序后的顺序 的开始位置
    - end: 文章信息列表从 按rule排序后的顺序 的结束位置
    - rule: 文章排序规则（创建时间/更新时间）
    """
    list = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_post_json(jsonlink, list, start, end, rule)


@app.get("/version", tags=["PUBLIC_API"], summary="返回版本信息")
async def version():
    """版本检查
    status:0 不需要更新；status:1 需要更新 status:2 检查更新失败
    """
    VERSION = scrapy_conf.VERSION
    api_json = {"status": 0, "current_version": VERSION}
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
                if not d.exception() and d.result():
                    api_json["latest_version"] = d.result()
                    break
            else:
                api_json["status"] = 2
    except:
        api_json["status"] = 2
        return api_json
    if VERSION != api_json["latest_version"]:
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


@app.get("/login_with_token", tags=["Manage"])
async def login_with_token(payload: str = Depends(login_with_token_)):
    return format_response.standard_response(message="Login success")


@app.post("/login", tags=["Manage"])
async def login(password: PassWord):
    return await login_(password.password)


@app.put("/update_settings", tags=["Manage"])
async def update_settings(fc_settings: item_fc_settings, payload: str = Depends(login_with_token_)):
    base_path = get_base_path()
    # fc_settings = json.dumps(fc_settings.dict())
    if tools.is_vercel():
        # github+vercel特殊处理
        dump_path = "/tmp/dump_settings.yaml"
        with open(dump_path, 'w', encoding="utf-8") as f:
            yaml.safe_dump(fc_settings.dict(), f)
        with open(dump_path, "rb") as f:
            data = f.read()
        # 需要将sqlite配置dump_settings.yaml上传
        gh_access_token = os.environ.get("GH_TOKEN", "")
        gh_name = os.environ.get("GH_NAME", "")
        gh_email = os.environ.get("GH_EMAIL", "")
        repo_name = "hexo-circle-of-friends"
        message = "Update dump_settings.yaml"
        resp = await create_or_update_file(gh_access_token, gh_name, gh_email, repo_name,
                                           "dump_settings.yaml",
                                           get_b64encoded_data(data), message)
        return format_response.standard_response(**resp)

    else:
        dump_path = os.path.join(base_path, "dump_settings.yaml")
        with open(dump_path, 'w', encoding="utf-8") as f:
            yaml.safe_dump(fc_settings.dict(), f)
    return format_response.standard_response()


@app.get("/read_settings", tags=["Manage"])
async def read_settings(payload: str = Depends(login_with_token_)):
    current_settings = get_user_settings()
    return format_response.standard_response(current_settings=current_settings)


# @app.put("/update_env", tags=["Manage"])
# async def update_env(fc_env: FcEnv, payload: str = Depends(login_with_token_)):
#     print(fc_env)
#     if settings["DEPLOY_TYPE"] == "github":
#
#         return "ok"


@app.get("/restart_api", tags=["Manage"])
async def restart_api(payload: str = Depends(login_with_token_)):
    os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == "__main__":
    if settings["DEPLOY_TYPE"] == "docker":
        uvicorn.run("main:app", host="0.0.0.0")
    elif settings["DEPLOY_TYPE"] == "server":
        EXPOSE_PORT = int(os.environ["EXPOSE_PORT"]) if os.environ["EXPOSE_PORT"] else 8000
        uvicorn.run("main:app", host="0.0.0.0", port=EXPOSE_PORT)
    else:
        uvicorn.run("main:app", host="0.0.0.0", reload=True)
