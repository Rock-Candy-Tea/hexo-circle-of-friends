# -*- coding:utf-8 -*-

import os
import json
import random
import requests
import leancloud
from leancloud.errors import LeanCloudError
from fastapi import Depends
from hexo_circle_of_friends.utils.process_time import time_compare
from api_dependencies import format_response, dependencies as dep
from api_dependencies.utils.validate_params import start_end_check
from api_dependencies.leancloud import security, db_interface
from jose import JWTError


def query_all(li, start: int = 0, end: int = -1, rule: str = "updated"):
    # Verify key
    db_interface.db_init()

    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('time')
    query.limit(1000)
    query.select('title', 'created', 'updated', 'link', 'author', 'avatar', 'createdAt')
    query_list = query.find()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('friendname', 'friendlink', 'firendimg', 'error')
    query_list_user = query_userinfo.find()

    # Result to arr
    data = {}
    friends_num = len(query_list_user)
    active_num = len(set([item.get('author') for item in query_list]))
    error_num = len([friend for friend in query_list_user if friend.get('error') == 'true'])
    article_num = len(query_list)
    last_updated_time = max([item.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') for item in query_list])

    # 检查start、end的合法性
    start, end, message = start_end_check(start, end, article_num)
    if message:
        return {"message": message}
    # 检查rule的合法性
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    data['statistical_data'] = {
        'friends_num': friends_num,
        'active_num': active_num,
        'error_num': error_num,
        'article_num': article_num,
        'last_updated_time': last_updated_time
    }

    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {}
        for elem in li:
            if elem == 'created':
                itemlist[elem] = item.get('created')
            elif elem == 'avatar':
                itemlist[elem] = item.get('avatar')
            else:
                itemlist[elem] = item.get(elem)
        article_data_init.append(itemlist)

    rules = []
    # list sort 是 稳定 的，这意味着当多个记录具有相同的键值时，将**保留其原始顺序**
    if rule == "created":
        rules.extend(["updated", "created"])
    else:
        rules.extend(["created", "updated"])
    for r in rules:
        try:
            article_data_init.sort(key=lambda x: x[r], reverse=True)
        except:
            return {"message": "sort error"}

    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    data['article_data'] = article_data[start:end]
    return data


def query_friend():
    # Verify key
    db_interface.db_init()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('friendname', 'friendlink', 'firendimg')
    query_list_user = query_userinfo.find()

    # Result to arr
    friend_list_json = []
    for item in query_list_user:
        itemlist = {
            'name': item.get('friendname'),
            'link': item.get('friendlink'),
            'avatar': item.get('firendimg')
        }
        friend_list_json.append(itemlist)

    return friend_list_json


def query_random_friend(num):
    # Verify key
    db_interface.db_init()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('friendname', 'friendlink', 'firendimg')
    query_list_user = query_userinfo.find()

    # Result to arr
    friend_list_json = []
    for item in query_list_user:
        itemlist = {
            'name': item.get('friendname'),
            'link': item.get('friendlink'),
            'avatar': item.get('firendimg')
        }
        friend_list_json.append(itemlist)
    try:
        if num < 1:
            return {"message": "param 'num' error"}
        elif num == 1:
            return random.choice(friend_list_json)
        elif num <= len(friend_list_json):
            return random.sample(friend_list_json, k=num)
        else:
            return random.sample(friend_list_json, k=len(friend_list_json))
    except:
        return {"message": "not found"}


def query_random_post(num):
    # Verify key
    db_interface.db_init()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)
    query_list = query.find()

    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {
            "title": item.get("title"),
            "created": item.get("created"),
            "updated": item.get("updated"),
            "link": item.get("link"),
            "author": item.get("author"),
            "avatar": item.get("avatar"),
        }
        article_data_init.append(itemlist)
    article_data_init.sort(key=lambda x: x["updated"], reverse=True)
    for item in article_data_init:
        article_data.append(item)
    # return random.choice(article_data)
    try:
        if num < 1:
            return {"message": "param 'num' error"}
        elif num == 1:
            return random.choice(article_data)
        elif num <= len(article_data):
            return random.sample(article_data, k=num)
        else:
            return random.sample(article_data, k=len(article_data))
    except:
        return {"message": "not found"}


def query_post(link, num, rule):
    # Verify key
    db_interface.db_init()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)
    query.select('title', 'created', 'updated', 'link', 'author', 'avatar', 'createdAt')
    query_list = query.find()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('friendname', 'friendlink', 'firendimg')
    query_list_user = query_userinfo.find()

    if link is None:
        link = random.choice(query_list_user).get('friendlink')
    api_json = {}
    if link.startswith('http'):
        links = link.split('/')[2]
    else:
        links = link

    author = None
    avatar = None
    article_data_init = []
    article_data = []
    for item in query_list:
        if links in item.get('link'):
            author = item.get('author')
            avatar = item.get('avatar')
            itemlist = {
                "title": item.get("title"),
                "link": item.get("link"),
                "created": item.get("created"),
                "updated": item.get("updated"),
            }
            article_data_init.append(itemlist)
    if not author:
        return {"message": "not found"}
    article_num = len(article_data_init)
    if num < 0 or num > min(article_num, 1000):
        num = min(article_num, 1000)
    api_json['statistical_data'] = {
        "name": author,
        "link": link,
        "avatar": avatar,
        "article_num": num
    }
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data_init.sort(key=lambda x: x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)
    api_json['article_data'] = article_data[:num]
    return api_json


def query_friend_status(days):
    # 初始化数据库连接
    db_interface.db_init()
    # 查询
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('time')
    query.limit(1000)
    query.select('updated', 'author')
    query_list = query.find()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('friendname', 'friendlink')
    query_list_user = query_userinfo.find()
    name_2_link_map = {user.get("friendname"): user.get("friendlink") for user in query_list_user}
    friend_status = {
        "total_friend_num": len(name_2_link_map),
        "total_lost_num": 0,
        "total_not_lost_num": 0,
        "lost_friends": {},
        "not_lost_friends": {},
    }
    not_lost_friends = {}
    for i in query_list:
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
    # Verify key
    db_interface.db_init()
    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)

    # Choose class
    query.select('title', 'created', 'updated', 'link', 'author', 'avatar', 'createdAt')
    query_list = query.find()

    headers = {
        "Cookie": "arccount62298=c; arccount62019=c",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66"
    }
    jsonhtml = requests.get(jsonlink, headers=headers).text
    linklist = set(json.loads(jsonhtml))

    api_json = {}
    article_data_init = []
    article_data = []
    linkinPubLibrary_set = set()
    for item in query_list:
        for link in linklist:
            if link.startswith('http'):
                links = link.split('/')[2]
            else:
                links = link
            if links in item.get('link'):
                linkinPubLibrary_set.add(link)
                itemlist = {}
                for elem in list:
                    itemlist[elem] = item.get(elem)
                article_data_init.append(itemlist)
                break

    article_num = len(article_data_init)
    if end == -1 or end > min(article_num, 1000):
        end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0:
        return {"message": "end error"}
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data_init.sort(key=lambda x: x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    friends_num = len(linklist)
    linkinPubLibrary_num = len(linkinPubLibrary_set)
    linknoninPub_list = [link for link in linklist if link not in linkinPubLibrary_set]
    linknoninPub_num = len(linknoninPub_list)
    last_updated_time = max([item.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') for item in query_list])

    api_json['statistical_data'] = {
        'friends_num': friends_num,
        'linkinPubLibrary_num': linkinPubLibrary_num,
        'linknoninPub_num': linknoninPub_num,
        'article_num': article_num,
        'last_updated_time': last_updated_time,
        'linknoninPub_list': linknoninPub_list
    }
    api_json['article_data'] = article_data[start:end]
    return api_json


async def login_with_token_(token: str = Depends(dep.oauth2_scheme)):
    # 获取或者创建（首次）secret_key
    secert_key = await security.get_secret_key()
    try:
        payload = dep.decode_access_token(token, secert_key)
    except JWTError:
        raise format_response.CredentialsException

    return payload


async def login_(password: str):
    db_interface.db_init()
    secret_key = await security.get_secret_key()

    auth = leancloud.Object.extend('auth')
    auth_db = auth()
    query = auth.query
    query.limit(10)

    try:
        query.select('password')
        res = query.first()
        obj_id = res.id
        # 保存了pwd，通过pwd验证
        if dep.verify_password(password, res.get("password")):
            # 更新token
            data = {"password_hash": res.get("password")}
            token = dep.encode_access_token(data, secret_key)
        else:
            # 401
            return format_response.CredentialsException
    except LeanCloudError as e:
        # 表不存在
        # turn plain pwd to hashed pwd
        password_hash = dep.create_password_hash(password)
        # 未保存pwd，生成对应token并保存
        data = {"password_hash": password_hash}
        token = dep.encode_access_token(data, secret_key)
        auth_db.set("password", password_hash)
        auth_db.save()
    except:
        return format_response.CredentialsException
    return format_response.standard_response(token=token)


async def db_reset_():
    db_interface.db_init()
    # 清除friend、post表
    friendlist_query = leancloud.Query('friend_list')
    friendlist = friendlist_query.limit(1000).find()
    leancloud.Object.destroy_all(friendlist)
    friendpoor_query = leancloud.Query('friend_poor')
    friendpoor = friendpoor_query.limit(1000).find()
    leancloud.Object.destroy_all(friendpoor)
    return format_response.standard_response()
