# -*- coding:utf-8 -*-
# Author：yyyz
import os
import random

from urllib import parse
from hexo_circle_of_friends import settings
from pymongo import MongoClient
from hexo_circle_of_friends.utils.process_time import time_compare


def db_init():
    if settings.DEBUG:
        URI = "mongodb+srv://root:@cluster0.wgfbv.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    else:
        URI = os.environ.get("MONGODB_URI")
    client = MongoClient(URI)
    db = client.fcircle
    posts = db.Post
    friends = db.Friend
    return posts, friends


def query_all(list, start: int = 0, end: int = -1, rule: str = "updated"):
    post_collection, friend_db_collection = db_init()
    article_num = post_collection.count_documents({})
    if end == -1:
        end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0 or end > min(article_num, 1000):
        return {"message": "end error"}
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
    _, friend_db_collection = db_init()
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
    _, friend_db_collection = db_init()
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
    post_collection, _ = db_init()
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
    post_collection, friend_db_collection = db_init()
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
    post_collection, friend_db_collection = db_init()
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
