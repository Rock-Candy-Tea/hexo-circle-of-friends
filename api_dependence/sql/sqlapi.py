# -*- coding:utf-8 -*-

from datetime import datetime
from urllib import parse
from tools.utils import get_user_settings
from db.models import Friend, Post
from sqlalchemy.sql.expression import desc, func

from api_dependence.sql.db_interface import db_init


def query_all(li, start: int = 0, end: int = 0, rule: str = "updated"):
    session = db_init()
    article_num = session.query(Post).count()

    # 检查rule的合法性
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    if start == 0 and end == 0:
        posts = session.query(Post).order_by(desc(rule)).all()
    else:
        posts = (
            session.query(Post)
            .order_by(desc(rule))
            .offset(start)
            .limit(end - start)
            .all()
        )

    last_update_time_results = (
        session.query(Post).limit(1000).with_entities(Post.createdAt).all()
    )
    last_update_time = max(x[0] for x in last_update_time_results)

    friends_num = session.query(Friend).count()
    active_num = session.query(Friend).filter_by(error=False).count()
    error_num = friends_num - active_num

    data = {
        "statistical_data": {
            "friends_num": friends_num,
            "active_num": active_num,
            "error_num": error_num,
            "article_num": article_num,
            "last_updated_time": last_update_time,
        },
    }

    post_data = []
    for k, post in enumerate(posts):
        item = {"floor": start + k + 1}
        for elem in li:
            item[elem] = getattr(post, elem)
        post_data.append(item)

    session.close()
    data["article_data"] = post_data  # type: ignore
    return data


def query_friend():
    session = db_init()
    friends = session.query(Friend).limit(1000).all()
    session.close()

    friend_list_json = []
    if friends:
        for friend in friends:
            item = {"name": friend.name, "link": friend.link, "avatar": friend.avatar}
            friend_list_json.append(item)
    else:
        # friends为空直接返回
        return {"message": "not found"}

    return friend_list_json


def query_random_friend(num):
    if num < 1:
        return {"message": "param 'num' error"}
    session = db_init()
    settings = get_user_settings()

    if settings["DATABASE"] == "sqlite":
        data = session.query(Friend).order_by(func.random()).limit(num).all()
    else:
        data = session.query(Friend).order_by(func.rand()).limit(num).all()
    session.close()
    friend_list_json = []
    if data:
        for d in data:
            itemlist = {"name": d.name, "link": d.link, "avatar": d.avatar}
            friend_list_json.append(itemlist)
    else:
        # data为空直接返回
        return {"message": "not found"}
    return friend_list_json[0] if len(friend_list_json) == 1 else friend_list_json


def query_random_post(num):
    if num < 1:
        return {"message": "param 'num' error"}
    session = db_init()
    settings = get_user_settings()
    if settings["DATABASE"] == "sqlite":
        data = session.query(Post).order_by(func.random()).limit(num).all()
    else:
        data = session.query(Post).order_by(func.rand()).limit(num).all()
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


def query_post(
    link,
    num,
    rule,
):
    session = db_init()
    if link is None:
        user = (
            session.query(Friend).filter_by(error=False).order_by(func.random()).first()
        )
        domain = parse.urlsplit(user.link).netloc # type: ignore
    else:
        domain = parse.urlsplit(link).netloc
        user = (
            session.query(Friend)
            .filter(Friend.link.like("%{:s}%".format(domain)))
            .first()
        )

    posts = (
        session.query(Post)
        .filter(Post.link.like("%{:s}%".format(domain)))
        .order_by(desc(rule))
        .limit(num if num > 0 else None)
        .all()
    )
    session.close()

    data = []
    for floor, post in enumerate(posts):
        itemlist = {
            "title": post.title,
            "link": post.link,
            "created": post.created,
            "updated": post.updated,
            "floor": floor + 1,
        }
        data.append(itemlist)

    if user:
        api_json = {
            "statistical_data": {
                "name": user.name,
                "link": user.link,
                "avatar": user.avatar,
                "article_num": len(posts),
            },
            "article_data": data,
        }
    else:
        # 如果user为空直接返回
        return {"message": "not found"}

    return api_json
