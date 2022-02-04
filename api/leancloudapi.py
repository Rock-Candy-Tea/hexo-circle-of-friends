# -*- coding:utf-8 -*-

import os
import json
import random
import requests
import leancloud
from hexo_circle_of_friends import settings

def db_init():
    if settings.DEBUG:
        leancloud.init(settings.LC_APPID, settings.LC_APPKEY)
    else:
        leancloud.init(os.environ["APPID"], os.environ["APPKEY"])

def query_all(list, start: int = 0, end: int = -1, rule: str = "updated"):
    # Verify key
    db_init()

    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('time')
    query.limit(1000)
    query.select('title', 'created', 'updated', 'link', 'author', 'headimg', 'createdAt')
    query_list = query.find()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('frindname', 'friendlink', 'firendimg', 'error')
    query_list_user = query_userinfo.find()

    # Result to arr
    data = {}
    friends_num = len(query_list_user)
    active_num = len(set([item.get('author') for item in query_list]))
    error_num = len([friend for friend in query_list_user if friend.get('error') == 'true'])
    article_num = len(query_list)
    last_updated_time = max([item.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') for item in query_list])

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
        for elem in list:
            if elem == 'created':
                itemlist[elem] = item.get('created')
            elif elem == 'avatar':
                itemlist[elem] = item.get('headimg')
            else:
                itemlist[elem] = item.get(elem)
        article_data_init.append(itemlist)

    if end == -1:
        end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0 or end > min(article_num, 1000):
        return {"message": "end error"}
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data_init.sort(key=lambda x: x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    data['article_data'] = article_data[start:end]
    return data


def query_friend(list):
    # Verify key
    db_init()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('frindname', 'friendlink', 'firendimg')
    query_list_user = query_userinfo.find()

    # Result to arr
    friend_list_json = []
    for item in query_list_user:
        itemlist = {
            'name': item.get('frindname'),
            'link': item.get('friendlink'),
            'avatar': item.get('firendimg')
        }
        friend_list_json.append(itemlist)

    return friend_list_json


def query_random_friend(list):
    # Verify key
    db_init()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('name', 'link', 'avatar', 'descr')
    query_list_user = query_userinfo.find()

    # Result to arr
    friend_list_json = []
    for item in query_list_user:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        friend_list_json.append(itemlist)

    return random.choice(friend_list_json)


def query_random_post(rule, list):
    # Verify key
    db_init()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)
    query_list = query.find()

    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        article_data_init.append(itemlist)

    article_data_init.sort(key=lambda x: x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    return random.choice(article_data)


def query_post(link, num, rule, list):
    # Verify key
    db_init()

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
    query_userinfo.select('name', 'link', 'avatar', 'descr')
    query_list_user = query_userinfo.find()

    if link is None:
        link = random.choice(query_list_user).get('link')
    author = None
    avatar = None
    article_num = None
    api_json = {}

    if link.startswith('http'):
        links = link.split('/')[2]
    else:
        links = link
    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {}
        if links in item.get('link'):
            if author is None:
                author = item.get('author')
            if avatar is None:
                avatar = item.get('avatar')
            for elem in list:
                itemlist[elem] = item.get(elem)
            article_data_init.append(itemlist)

    article_num = len(article_data_init)
    api_json['statistical_data'] = {
        "author": author,
        "link": link,
        "avatar": avatar,
        "article_num": article_num
    }

    if num < 0 or num > min(article_num, 1000):
        num = min(article_num, 1000)
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


def query_post_json(jsonlink, list, start, end, rule):
    # Verify key
    db_init()

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
    linklist = json.loads(jsonhtml)

    linkset = set()
    for link in linklist:
        linkset.add(link)

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

    friends_num = len(linkset)
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