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
from multiprocessing import Process
from hexo_circle_of_friends.utils.project import get_user_settings, get_base_path
from hexo_circle_of_friends import scrapy_conf
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api_dependencies.items import PassWord, GitHubEnv, VercelEnv, ServerEnv, FcSettings as item_fc_settings
from api_dependencies.utils.github_interface import bulk_create_or_update_secret, create_or_update_file, \
    get_b64encoded_data, crawl_now, check_crawler_status
from api_dependencies.utils.vercel_interface import bulk_create_or_update_env, get_envs
from api_dependencies import format_response, tools

settings = get_user_settings()
if settings["DATABASE"] == 'leancloud':
    from api_dependencies.leancloud.leancloudapi import *
elif settings["DATABASE"] == "mysql" or settings["DATABASE"] == "sqlite":
    from api_dependencies.sql.sqlapi import *
elif settings["DATABASE"] == "mongodb":
    from api_dependencies.mongodb.mongodbapi import *

OUTDATE_CLEAN = settings["OUTDATE_CLEAN"]

app = FastAPI(docs_url=None, redoc_url=None)

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
    - rule: 文章排序规则（创建时间created/更新时间updated）
    """
    list_ = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    return query_all(list_, start, end, rule)


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
                "https://fcircle-doc.yyyzyyyz.cn/version.txt",
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
        try:
            dump_path = os.path.join(base_path, "dump_settings.yaml")
            with open(dump_path, 'w', encoding="utf-8") as f:
                yaml.safe_dump(fc_settings.dict(), f)
            return format_response.standard_response(message="保存成功")
        except:
            return format_response.standard_response(code=400, message="上传配置失败")


@app.get("/read_settings", tags=["Manage"])
async def read_settings(payload: str = Depends(login_with_token_)):
    current_settings = get_user_settings()
    return format_response.standard_response(current_settings=current_settings)


@app.put("/update_github_env", tags=["Manage"])
async def update_github_env(github_env: GitHubEnv, payload: str = Depends(login_with_token_)):
    if settings["DEPLOY_TYPE"] != "github":
        return format_response.standard_response(code=400, message="当前部署方式不是github")
    envs = github_env.dict(exclude_unset=True)
    # 优先从body中获取，其次从环境变量获取
    gh_access_token = envs["GH_TOKEN"] if envs.get("GH_TOKEN") else os.environ.get("GH_TOKEN")
    gh_name = envs.get("GH_NAME") if envs.get("GH_NAME") else os.environ.get("GH_NAME")
    repo_name = "hexo-circle-of-friends"
    if not gh_access_token or not gh_name:
        return format_response.standard_response(code=400, message="缺少环境变量GH_TOKEN或GH_NAME")

    resp = await bulk_create_or_update_secret(gh_access_token, gh_name, repo_name, envs)
    return format_response.standard_response(details=resp)


@app.put("/update_vercel_env", tags=["Manage"])
async def update_vercel_env(vercel_env: VercelEnv, payload: str = Depends(login_with_token_)):
    if not tools.is_vercel():
        return format_response.standard_response(code=400, message="当前不是vercel环境")
    envs = vercel_env.dict(exclude_unset=True)
    # 优先从body中获取，其次从环境变量获取
    vercel_access_token = envs["VERCEL_ACCESS_TOKEN"] if envs.get("VERCEL_ACCESS_TOKEN") else os.environ.get(
        "VERCEL_ACCESS_TOKEN")
    if not vercel_access_token:
        return format_response.standard_response(code=400, message="缺少环境变量VERCEL_ACCESS_TOKEN")
    project_name = "hexo-circle-of-friends"

    resp = await bulk_create_or_update_env(vercel_access_token, project_name, envs)
    return format_response.standard_response(details=resp)


@app.put("/update_server_env", tags=["Manage"])
async def update_server_env(server_env: ServerEnv, payload: str = Depends(login_with_token_)):
    if settings["DEPLOY_TYPE"] == "github":
        return format_response.standard_response(code=400, message="当前部署方式不是server或docker")
    base_path = get_base_path()
    with open(os.path.join(base_path, "env.json"), "w") as f:
        json.dump(server_env.dict(), f)
    return format_response.standard_response(message="保存成功")


@app.get("/restart_api", tags=["Manage"])
async def restart_api(payload: str = Depends(login_with_token_)):
    if settings["DEPLOY_TYPE"] == "github":
        gh_access_token = os.environ.get("GH_TOKEN", "")
        gh_name = os.environ.get("GH_NAME", "")
        gh_email = os.environ.get("GH_EMAIL", "")
        repo_name = "hexo-circle-of-friends"
        message = "auto restart"
        data = b"1"
        await create_or_update_file(gh_access_token, gh_name, gh_email, repo_name,
                                    "restartfile",
                                    get_b64encoded_data(data), message)
    else:
        base_path = get_base_path()
        kill_self = r"ps -ef | egrep 'python3 -u|python3 -c' | grep -v grep | awk '{print $2}' | xargs kill -9"
        server_sh = f"#!/bin/bash\nsleep 10s\n{kill_self}\nexport BASE_PATH={base_path}\n" + "export PYTHONPATH=${PYTHONPATH}:${BASE_PATH}\n"

        env_json_path = os.path.join(base_path, "env.json")
        if os.path.exists(env_json_path):
            with open(env_json_path, "r") as f:
                envs = json.load(f)
        else:
            envs = {}
        with open("temp.sh", "w") as f:
            for name, value in envs.items():
                if value is not None:
                    server_sh += f"export {name}={value}\n"
            server_sh += "nohup python3 -u ${BASE_PATH}/api/main.py >/tmp/api_stdout.log 2>&1 &\nnohup python3 -u ${" \
                         "BASE_PATH}/hexo_circle_of_friends/run.py > /tmp/crawler_stdout.log 2>&1 & "

            f.write(server_sh.strip())
        os.popen("chmod a+x temp.sh && nohup ./temp.sh >/dev/null 2>&1 &")
        return format_response.standard_response(message="已重启")


@app.get("/read_envs", tags=["Manage"])
async def read_envs(payload: str = Depends(login_with_token_)):
    if settings["DEPLOY_TYPE"] == "github":
        # 从环境变量获取vercel_access_token
        vercel_access_token = os.environ.get("VERCEL_ACCESS_TOKEN")
        if not vercel_access_token:
            return format_response.standard_response(code=400, message="缺少环境变量VERCEL_ACCESS_TOKEN")
        project_name = "hexo-circle-of-friends"
        resp_envs = await get_envs(vercel_access_token, project_name)
    else:
        # docker/server
        resp_envs = ServerEnv()
    return format_response.standard_response(current_envs=resp_envs)


@app.get("/run_crawl_now", tags=["Manage"])
async def run_crawl_now(payload: str = Depends(login_with_token_)):
    if settings["DEPLOY_TYPE"] == "github":
        # 获取gh_access_token
        gh_access_token = os.environ.get("GH_TOKEN")
        gh_name = os.environ.get("GH_NAME")
        if not gh_access_token or not gh_name:
            return format_response.standard_response(code=400, message="缺少环境变量GH_TOKEN或GH_NAME")
        repo_name = "hexo-circle-of-friends"
        resp = await crawl_now(gh_access_token, gh_name, repo_name)
    else:
        # docker/server
        from hexo_circle_of_friends.run import main
        try:
            process = Process(target=main)
            process.start()
            resp = {"code": 200, "message": "运行成功"}
        except:
            resp = {"code": 500, "message": "运行失败"}
    return format_response.standard_response(code=resp["code"], message=resp["message"])


@app.get("/crawler_status", tags=["Manage"])
async def crawler_status(payload: str = Depends(login_with_token_)):
    """
    查看crawler运行状态
    status: 运行中；未运行；未知
    """
    if settings["DEPLOY_TYPE"] == "github":
        # 获取gh_access_token
        gh_access_token = os.environ.get("GH_TOKEN")
        gh_name = os.environ.get("GH_NAME")
        if not gh_access_token or not gh_name:
            return format_response.standard_response(code=400, message="缺少环境变量GH_TOKEN或GH_NAME")
        repo_name = "hexo-circle-of-friends"
        resp = await check_crawler_status(gh_access_token, gh_name, repo_name)
    else:
        # docker/server
        resp = {"code": 200, "message": "检查成功"}
        # restart_api:两个run；run_crawl_now两个main
        check_restart_api = int(os.popen(
            "ps -ef | egrep 'hexo_circle_of_friends/run.py' | grep -v grep | wc -l").read().strip())
        check_run_crawl_now = int(os.popen("ps -ef | egrep 'api/main.py' | grep -v grep | wc -l").read().strip())
        if check_restart_api <= 1 and check_run_crawl_now == 1:
            resp["status"] = "未运行"
        elif check_restart_api == 2 or check_run_crawl_now == 2:
            resp["status"] = "运行中"
        else:
            resp["code"] = 500
            resp["message"] = "检查运行状态失败"
            resp["status"] = "未知"
    return format_response.standard_response(**resp)

@app.delete("/db_reset", tags=["Manage"])
async def db_reset(payload: str = Depends(login_with_token_)):
    """
    清空数据库中友链、文章表
    """
    return await db_reset_()


if __name__ == "__main__":
    if settings["DEPLOY_TYPE"] == "docker":
        uvicorn.run("main:app", host="0.0.0.0")
    elif settings["DEPLOY_TYPE"] == "server":
        EXPOSE_PORT = int(os.environ["EXPOSE_PORT"]) if os.environ.get("EXPOSE_PORT") else 8000
        uvicorn.run("main:app", host="0.0.0.0", port=EXPOSE_PORT)
    else:
        uvicorn.run("main:app", host="0.0.0.0", reload=True)
