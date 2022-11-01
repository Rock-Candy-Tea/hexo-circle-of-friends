# -*- coding:utf-8 -*-

import os
import json
import requests
from fastapi import Depends
from urllib import parse
from jose import JWTError
from hexo_circle_of_friends.utils.project import get_user_settings
from hexo_circle_of_friends.models import Friend, Post, Auth
from sqlalchemy.sql.expression import desc, func
from hexo_circle_of_friends.utils.process_time import time_compare
from api_dependencies.utils.validate_params import start_end_check
from api_dependencies.utils.github_interface import create_or_update_file, get_b64encoded_data
from api_dependencies.sql import db_interface, security
from api_dependencies import format_response, tools, dependencies as dep


async def vercel_update_db():
    """
    vercel环境需要上传data.db到github
    :return:
    """
    # github+vercel将db上传
    db_path = "/tmp/data.db"
    with open(db_path, "rb") as f:
        data = f.read()
    gh_access_token = os.environ.get("GH_TOKEN", "")
    gh_name = os.environ.get("GH_NAME", "")
    gh_email = os.environ.get("GH_EMAIL", "")
    repo_name = "hexo-circle-of-friends"
    message = "Update data.db"
    await create_or_update_file(gh_access_token, gh_name, gh_email, repo_name,
                                "data.db",
                                get_b64encoded_data(data), message)


def query_all(li, start: int = 0, end: int = -1, rule: str = "updated"):
    session = db_interface.db_init()
    article_num = session.query(Post).count()
    # 检查start、end的合法性
    start, end, message = start_end_check(start, end, article_num)
    if message:
        return {"message": message}
    # 检查rule的合法性
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    posts = session.query(Post).order_by(desc(rule)).offset(start).limit(end - start).all()
    last_update_time = session.query(Post).limit(1000).with_entities(Post.createAt).all()
    last_update_time = max(x["createAt"].strftime("%Y-%m-%d %H:%M:%S") for x in last_update_time)

    friends_num = session.query(Friend).count()
    active_num = session.query(Friend).filter_by(error=False).count()
    error_num = friends_num - active_num

    data = {}
    data['statistical_data'] = {
        'friends_num': friends_num,
        'active_num': active_num,
        'error_num': error_num,
        'article_num': article_num,
        'last_updated_time': last_update_time
    }

    post_data = []
    for k in range(len(posts)):
        item = {'floor': start + k + 1}
        for elem in li:
            item[elem] = getattr(posts[k], elem)
        post_data.append(item)
    session.close()
    data['article_data'] = post_data
    return data


def query_friend():
    session = db_interface.db_init()
    friends = session.query(Friend).limit(1000).all()
    session.close()

    friend_list_json = []
    if friends:
        for friend in friends:
            item = {
                'name': friend.name,
                'link': friend.link,
                'avatar': friend.avatar
            }
            friend_list_json.append(item)
    else:
        # friends为空直接返回
        return {"message": "not found"}

    return friend_list_json


def query_random_friend(num):
    if num < 1:
        return {"message": "param 'num' error"}
    session = db_interface.db_init()
    settings = get_user_settings()
    if settings["DATABASE"] == "sqlite":
        data: list = session.query(Friend).order_by(func.random()).limit(num).all()
    else:
        data: list = session.query(Friend).order_by(func.rand()).limit(num).all()
    session.close()
    friend_list_json = []
    if data:
        for d in data:
            itemlist = {
                'name': d.name,
                'link': d.link,
                'avatar': d.avatar
            }
            friend_list_json.append(itemlist)
    else:
        # data为空直接返回
        return {"message": "not found"}
    return friend_list_json[0] if len(friend_list_json) == 1 else friend_list_json


def query_random_post(num):
    if num < 1:
        return {"message": "param 'num' error"}
    session = db_interface.db_init()
    settings = get_user_settings()
    if settings["DATABASE"] == "sqlite":
        data: list = session.query(Post).order_by(func.random()).limit(num).all()
    else:
        data: list = session.query(Post).order_by(func.rand()).limit(num).all()
    session.close()
    post_list_json = []
    if data:
        for d in data:
            itemlist = {
                "title": d.title,
                "created": d.created,
                "updated": d.updated,
                "link": d.link,
                "author": d.author,
                "avatar": d.avatar,
            }
            post_list_json.append(itemlist)
    else:
        # data为空直接返回
        return {"message": "not found"}
    return post_list_json[0] if len(post_list_json) == 1 else post_list_json


def query_post(link, num, rule, ):
    session = db_interface.db_init()
    if link is None:
        user = session.query(Friend).filter_by(error=False).order_by(func.random()).first()
        domain = parse.urlsplit(user.link).netloc
    else:
        domain = parse.urlsplit(link).netloc
        user = session.query(Friend).filter(Friend.link.like("%{:s}%".format(domain))).first()

    posts = session.query(Post).filter(Post.link.like("%{:s}%".format(domain))).order_by(desc(rule)).limit(
        num if num > 0 else None).all()
    session.close()

    data = []
    for floor, post in enumerate(posts):
        itemlist = {
            "title": post.title,
            "link": post.link,
            "created": post.created,
            "updated": post.updated,
            "floor": floor + 1
        }
        data.append(itemlist)

    if user:
        api_json = {
            "statistical_data": {
                "name": user.name,
                "link": user.link,
                "avatar": user.avatar,
                "article_num": len(posts)
            },
            "article_data": data
        }
    else:
        # 如果user为空直接返回
        return {"message": "not found"}

    return api_json


def query_friend_status(days):
    # 初始化数据库连接
    session = db_interface.db_init()
    # 查询
    posts = session.query(Post).all()
    friends = session.query(Friend).all()
    name_2_link_map = {user.name: user.link for user in friends}
    friend_status = {
        "total_friend_num": len(name_2_link_map),
        "total_lost_num": 0,
        "total_not_lost_num": 0,
        "lost_friends": {},
        "not_lost_friends": {},
    }
    not_lost_friends = {}
    for i in posts:
        if not time_compare(i.updated, days):
            # 未超过指定天数，未失联
            if name_2_link_map.get(i.author):
                not_lost_friends[i.author] = name_2_link_map.pop(i.author)
            else:
                pass
    # 统计信息更新，失联友链更新
    friend_status["total_not_lost_num"] = len(not_lost_friends)
    friend_status["total_lost_num"] = friend_status["total_friend_num"] - friend_status["total_not_lost_num"]
    friend_status["not_lost_friends"] = not_lost_friends
    friend_status["lost_friends"] = name_2_link_map
    return friend_status


def query_post_json(jsonlink, list, start, end, rule):
    session = db_interface.db_init()

    headers = {
        "Cookie": "arccount62298=c; arccount62019=c",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66"
    }
    jsonhtml = requests.get(jsonlink, headers=headers).text
    linklist = set(json.loads(jsonhtml))
    if not linklist:
        # 如果为空直接返回
        return {"message": "not found"}

    posts = []
    active_list = []
    for link in linklist:
        domain = parse.urlsplit(link).netloc
        data = session.query(Post).filter(Post.link.like("%{:s}%".format(domain))).all()
        if data:
            posts += data
            active_list.append(link)

    posts.sort(key=lambda x: getattr(x, rule), reverse=True)
    post_num = len(posts)
    last_update_time = max(x.createAt.strftime("%Y-%m-%d %H:%M:%S") for x in posts)

    if end == -1:
        end = min(post_num, 1000)
    if start < 0 or start >= min(post_num, 1000):
        return {"message": "start error"}
    if end <= 0 or end > min(post_num, 1000):
        return {"message": "end error"}
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    session.close()

    friends_num = len(linklist)
    active_num = len(active_list)
    error_list = [link for link in linklist if link not in active_list]

    post_data = []
    for k in range(start, end):
        item = {'floor': k + 1}
        for elem in list:
            item[elem] = getattr(posts[k], elem)
        post_data.append(item)

    data = {}
    data['statistical_data'] = {
        'friends_num': friends_num,
        'linkinPubLibrary_num': active_num,
        'linknoninPub_num': friends_num - active_num,
        'article_num': post_num,
        'last_updated_time': last_update_time,
        'linknoninPub_list': error_list
    }
    data['article_data'] = post_data
    return data


async def login_with_token_(token: str = Depends(dep.oauth2_scheme)):
    # 获取或者创建（首次）secret_key
    secert_key = await security.get_secret_key()
    try:
        payload = dep.decode_access_token(token, secert_key)
    except JWTError:
        raise format_response.CredentialsException

    return payload


async def login_(password: str):
    session = db_interface.db_init()
    auth = session.query(Auth).all()
    # 获取或者创建（首次）secret_key
    secret_key = await security.get_secret_key()
    if not auth:
        # turn plain pwd to hashed pwd
        password_hash = dep.create_password_hash(password)
        # 未保存pwd，生成对应token并保存
        data = {"password_hash": password_hash}
        token = dep.encode_access_token(data, secret_key)
        tb_obj = Auth(password=password_hash)
        session.add(tb_obj)
        session.commit()
        session.close()
        if tools.is_vercel():
            await vercel_update_db()
    elif len(auth) == 1:
        # 保存了pwd，通过pwd验证
        if dep.verify_password(password, auth[0].password):
            # 更新token
            data = {"password_hash": auth[0].password}
            token = dep.encode_access_token(data, secret_key)
        else:
            # 401
            return format_response.CredentialsException
    else:
        # 401
        return format_response.CredentialsException

    return format_response.standard_response(token=token)


async def db_reset_():
    session = db_interface.db_init()
    # 清除friend、post表
    session.query(Friend).delete()
    session.query(Post).delete()
    session.commit()
    session.close()
    if tools.is_vercel():
        await vercel_update_db()
    return format_response.standard_response()
