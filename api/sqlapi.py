# -*- coding:utf-8 -*-

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import requests
from urllib import parse
from hexo_circle_of_friends import settings
from sqlalchemy import create_engine
from hexo_circle_of_friends.models import Friend, Post
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql.expression import desc, func


def db_init():
    if settings.DEBUG:
        if settings.DATABASE == "sqlite":
            conn = "sqlite:///" + BASE_DIR + "/data.db" + "?check_same_thread=False"
        elif settings.DATABASE == "mysql":
            conn = "mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8mb4" \
                   % ("root", "123456", "localhost", "test")
    else:
        if settings.DATABASE == "sqlite":
            conn = "sqlite:///" + BASE_DIR + "/data.db" + "?check_same_thread=False"
        elif settings.DATABASE == "mysql":
            conn = "mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4" \
                   % (os.environ["MYSQL_USERNAME"], os.environ["MYSQL_PASSWORD"], os.environ["MYSQL_IP"]
                      , os.environ["MYSQL_PORT"], os.environ["MYSQL_DB"])
    try:
        engine = create_engine(conn, pool_recycle=-1)
    except:
        raise Exception("MySQL连接失败")
    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)
    return session


def query_all(list, start: int = 0, end: int = -1, rule: str = "updated"):
    session = db_init()
    article_num = session.query(Post).count()
    if end == -1:
        end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0 or end > min(article_num, 1000):
        return {"message": "end error"}
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
        for elem in list:
            item[elem] = getattr(posts[k], elem)
        post_data.append(item)
    session.close()
    data['article_data'] = post_data
    return data


def query_friend():
    session = db_init()
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


def query_random_friend():
    session = db_init()
    data: Friend = session.query(Friend).order_by(func.random()).first()
    session.close()
    if data:
        itemlist = {
            'name': data.name,
            'link': data.link,
            'avatar': data.avatar
        }
    else:
        # data为空直接返回
        return {"message": "not found"}

    return itemlist


def query_random_post():
    session = db_init()
    data: Post = session.query(Post).order_by(func.random()).first()
    session.close()
    if data:
        itemlist = {
            "title": data.title,
            "created": data.created,
            "updated": data.updated,
            "link": data.link,
            "author": data.author,
            "avatar": data.avatar,
        }
    else:
        # data为空直接返回
        return {"message": "not found"}
    return itemlist


def query_post(link, num, rule, ):
    session = db_init()
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
                "author": user.name,
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


def query_post_json(jsonlink, list, start, end, rule):
    session = db_init()

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
