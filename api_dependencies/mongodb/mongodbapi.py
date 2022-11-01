# -*- coding:utf-8 -*-
# Author：yyyz
import os
import random
from fastapi import Depends
from urllib import parse
from hexo_circle_of_friends.utils.process_time import time_compare
from api_dependencies.utils.validate_params import start_end_check
from api_dependencies.mongodb import db_interface, security
from api_dependencies import format_response, dependencies as dep
from jose import JWTError


def query_all(list, start: int = 0, end: int = -1, rule: str = "updated"):
    session = db_interface.db_init()
    post_collection, friend_db_collection = session.Post, session.Friend
    article_num = post_collection.count_documents({})
    # 检查start、end的合法性
    start, end, message = start_end_check(start, end, article_num)
    if message:
        return {"message": message}
    # 检查rule的合法性
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    posts = post_collection.find({}, {'_id': 0, "rule": 0}).sort([(rule, -1)]).limit(end - start).skip(start)
    last_update_time = "1970-01-01 00:00:00"
    post_data = []
    for k, post in enumerate(posts):
        try:
            last_update_time = max(last_update_time, post.pop("createdAt"))
            item = {'floor': start + k + 1}
            item.update(post)
            post_data.append(item)
        except KeyError:
            pass

    friends_num = friend_db_collection.count_documents({})
    active_num = friend_db_collection.count_documents({"error": False})
    error_num = friends_num - active_num

    data = {}
    data['statistical_data'] = {
        'friends_num': friends_num,
        'active_num': active_num,
        'error_num': error_num,
        'article_num': article_num,
        'last_updated_time': last_update_time
    }

    data['article_data'] = post_data
    return data


def query_friend():
    session = db_interface.db_init()
    friend_db_collection = session.Friend
    friends = friend_db_collection.find({}, {"_id": 0, "createdAt": 0, "error": 0})
    friend_list_json = []
    if friends:
        for friend in friends:
            friend_list_json.append(friend)
    else:
        # friends为空直接返回
        return {"message": "not found"}
    return friend_list_json


def query_random_friend(num):
    session = db_interface.db_init()
    friend_db_collection = session.Friend
    friends = list(friend_db_collection.find({}, {"_id": 0, "createdAt": 0, "error": 0}))
    try:
        if num < 1:
            return {"message": "param 'num' error"}
        elif num == 1:
            return random.choice(friends)
        elif num <= len(friends):
            return random.sample(friends, k=num)
        else:
            return random.sample(friends, k=len(friends))
    except:
        return {"message": "not found"}


def query_random_post(num):
    session = db_interface.db_init()
    post_collection = session.Post
    posts = list(post_collection.find({}, {'_id': 0, "rule": 0, "createdAt": 0}))
    posts_num = post_collection.count_documents({})
    try:
        if num < 1:
            return {"message": "param 'num' error"}
        elif num == 1:
            return random.choice(posts)
        elif num <= len(posts):
            return random.sample(posts, k=num)
        else:
            return random.sample(posts, k=len(posts))
    except:
        return {"message": "not found"}


def query_post(link, num, rule):
    session = db_interface.db_init()
    post_collection, friend_db_collection = session.Post, session.Friend
    if link is None:
        friend = query_random_friend(1)
        domain = parse.urlsplit(friend.get("link")).netloc
    else:
        domain = parse.urlsplit(link).netloc
        friend = friend_db_collection.find_one({'link': {'$regex': domain}}, {"_id": 0, "createdAt": 0, "error": 0})

    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    posts = post_collection.find(
        {'link': {'$regex': domain}},
        {'_id': 0, "rule": 0, "createdAt": 0, "avatar": 0, "author": 0}
    ).sort([(rule, -1)]).limit(num if num > 0 else 0)

    data = []
    for floor, post in enumerate(posts):
        post["floor"] = floor + 1
        data.append(post)
    if friend:
        friend["article_num"] = len(data)
        api_json = {"statistical_data": friend, "article_data": data}
    else:
        # 如果user为空直接返回
        return {"message": "not found"}
    return api_json


def query_friend_status(days):
    # 初始化数据库连接
    session = db_interface.db_init()
    post_collection, friend_db_collection = session.Post, session.Friend
    # 查询
    posts = list(post_collection.find({}, {'_id': 0, "rule": 0, "createdAt": 0, "created": 0, "avatar": 0, "link": 0,
                                           "title": 0}))
    friends = list(friend_db_collection.find({}, {"_id": 0, "createdAt": 0, "error": 0, "avatar": 0}))
    name_2_link_map = {user.get("name"): user.get("link") for user in friends}
    friend_status = {
        "total_friend_num": len(name_2_link_map),
        "total_lost_num": 0,
        "total_not_lost_num": 0,
        "lost_friends": {},
        "not_lost_friends": {},
    }
    not_lost_friends = {}
    for i in posts:
        if not time_compare(i.get("updated"), days):
            # 未超过指定天数，未失联
            if name_2_link_map.get(i.get("author")):
                not_lost_friends[i.get("author")] = name_2_link_map.pop(i.get("author"))
            else:
                pass
    # 统计信息更新，失联友链更新
    friend_status["total_not_lost_num"] = len(not_lost_friends)
    friend_status["total_lost_num"] = friend_status["total_friend_num"] - friend_status["total_not_lost_num"]
    friend_status["not_lost_friends"] = not_lost_friends
    friend_status["lost_friends"] = name_2_link_map
    return friend_status


def query_post_json(jsonlink, list, start, end, rule):
    return {"message": "not found"}


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
    auth = session.auth
    # 查询数量
    auth_count = auth.count_documents({})
    # 查询结果
    auth_res = auth.find_one({})
    # 获取或者创建（首次）secret_key
    secret_key = await security.get_secret_key()
    if auth_count == 0:
        # turn plain pwd to hashed pwd
        password_hash = dep.create_password_hash(password)
        # 未保存pwd，生成对应token并保存
        data = {"password_hash": password_hash}
        token = dep.encode_access_token(data, secret_key)
        auth.insert_one({"password": password_hash})
    elif auth_count == 1:
        # 保存了pwd，通过pwd验证
        if dep.verify_password(password, auth_res["password"]):
            # 更新token
            data = {"password_hash": auth_res["password"]}
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
    post_collection, friend_db_collection = session.Post, session.Friend
    friend_db_collection.delete_many({})
    post_collection.delete_many({})

    return format_response.standard_response()
