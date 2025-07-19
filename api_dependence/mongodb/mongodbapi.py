# -*- coding:utf-8 -*-
# Author：yyyz
import os
import random
from urllib import parse
# from hexo_circle_of_friends.utils.process_time import time_compare
from api_dependence.mongodb import db_interface


def query_all(list, start: int = 0, end: int = -1, rule: str = "updated"):
    session = db_interface.db_init()
    post_collection, friend_db_collection = session.Post, session.Friend
    article_num = post_collection.count_documents({})
    # # 检查start、end的合法性
    # start, end, message = start_end_check(start, end, article_num)
    # if message:
    #     return {"message": message}
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
        domain = parse.urlsplit(friend.get("link")).netloc # type: ignore
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
        friend["article_num"] = len(data) # type: ignore
        api_json = {"statistical_data": friend, "article_data": data}
    else:
        # 如果user为空直接返回
        return {"message": "not found"}
    return api_json






