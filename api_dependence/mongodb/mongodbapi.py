# -*- coding:utf-8 -*-
# Author：yyyz
import random
from urllib import parse

# from hexo_circle_of_friends.utils.process_time import time_compare
from api_dependence.mongodb import db_interface


def query_all(li, start: int = 0, end: int = 0, rule: str = "updated"):
    """查询所有文章，包含摘要信息（与SQL版本一致）"""
    session = db_interface.db_init()
    post_collection = session.Post
    friend_db_collection = session.Friend

    article_num = post_collection.count_documents({})

    # 检查rule的合法性
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    # 构建聚合管道，实现LEFT JOIN功能
    pipeline = [
        # 1. 左连接 ArticleSummaries 集合
        {
            "$lookup": {
                "from": "ArticleSummaries",
                "localField": "link",
                "foreignField": "link",
                "as": "summary_info",
            }
        },
        # 2. 展开 summary_info 数组（如果存在）
        {"$addFields": {"summary_data": {"$arrayElemAt": ["$summary_info", 0]}}},
        # 3. 投影字段，选择需要的字段
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "created": 1,
                "updated": 1,
                "link": 1,
                "author": 1,
                "avatar": 1,
                "createdAt": 1,
                "summary": {"$ifNull": ["$summary_data.summary", None]},
                "ai_model": {"$ifNull": ["$summary_data.ai_model", None]},
                "summary_created_at": {"$ifNull": ["$summary_data.createdAt", None]},
                "summary_updated_at": {"$ifNull": ["$summary_data.updatedAt", None]},
            }
        },
        # 4. 排序
        {"$sort": {rule: -1}},
    ]

    # 5. 如果需要分页，添加skip和limit
    if start != 0 or end != 0:
        pipeline.append({"$skip": start})
        pipeline.append({"$limit": end - start})

    # 执行聚合查询
    posts_with_summary = list(post_collection.aggregate(pipeline))

    # 计算last_update_time
    last_update_time_results = list(
        post_collection.find({}, {"createdAt": 1, "_id": 0}).limit(1000)
    )
    if last_update_time_results:
        last_update_time = max(
            doc.get("createdAt", "1970-01-01 00:00:00")
            for doc in last_update_time_results
        )
    else:
        last_update_time = "1970-01-01 00:00:00"

    # 统计朋友信息
    friends_num = friend_db_collection.count_documents({})
    active_num = friend_db_collection.count_documents({"error": False})
    error_num = friends_num - active_num

    # 构建返回数据
    data = {
        "statistical_data": {
            "friends_num": friends_num,
            "active_num": active_num,
            "error_num": error_num,
            "article_num": article_num,
            "last_updated_time": last_update_time,
        }
    }

    # 处理文章数据
    post_data = []
    for k, post in enumerate(posts_with_summary):
        item = {"floor": start + k + 1}

        # 添加请求的字段
        for elem in li:
            item[elem] = post.get(elem)

        # 添加摘要相关字段
        item["summary"] = post.get("summary")
        item["ai_model"] = post.get("ai_model")
        item["summary_created_at"] = post.get("summary_created_at")
        item["summary_updated_at"] = post.get("summary_updated_at")

        post_data.append(item)

    data["article_data"] = post_data
    return data


def query_friend():
    session = db_interface.db_init()
    friend_db_collection = session.Friend
    friends = friend_db_collection.find({}, {"_id": 0})
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
    friends = list(friend_db_collection.find({}, {"_id": 0}))
    try:
        if num < 1:
            return {"message": "param 'num' error"}
        elif num == 1:
            return [random.choice(friends)]
        elif num <= len(friends):
            return random.sample(friends, k=num)
        else:
            return random.sample(friends, k=len(friends))
    except Exception:
        return {"message": "not found"}


def query_random_post(num):
    session = db_interface.db_init()
    post_collection = session.Post
    posts = list(post_collection.find({}, {"_id": 0, "floor": 0}))
    try:
        if num < 1:
            return {"message": "param 'num' error"}
        elif num == 1:
            return [random.choice(posts)]
        elif num <= len(posts):
            return random.sample(posts, k=num)
        else:
            return random.sample(posts, k=len(posts))
    except Exception:
        return {"message": "not found"}


def query_post(link, num, rule):
    session = db_interface.db_init()
    post_collection, friend_db_collection = session.Post, session.Friend
    if link is None:
        friend = query_random_friend(1)
        domain = parse.urlsplit(friend.get("link")).netloc  # type: ignore
    else:
        domain = parse.urlsplit(link).netloc
        friend = friend_db_collection.find_one(
            {"link": {"$regex": domain}}, {"_id": 0, "createdAt": 0, "error": 0}
        )

    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}

    posts = (
        post_collection.find(
            {"link": {"$regex": domain}},
            {"_id": 0, "rule": 0, "createdAt": 0},
        )
        .sort([(rule, -1)])
        .limit(num if num > 0 else 0)
    )

    data = []
    for floor, post in enumerate(posts):
        post["floor"] = floor + 1
        data.append(post)
    if friend:
        friend["article_num"] = len(data)  # type: ignore
        api_json = {"statistical_data": friend, "article_data": data}
    else:
        # 如果user为空直接返回
        return {"message": "not found"}
    return api_json


def query_summary(link):
    """查询指定链接的文章摘要"""
    session = db_interface.db_init()
    summary_collection = session.ArticleSummaries

    # 查找匹配的摘要
    summary = summary_collection.find_one(
        {"link": link},
        {"_id": 0},  # 排除MongoDB的_id字段
    )

    if summary:
        return {
            "link": summary.get("link"),
            "summary": summary.get("summary"),
            "ai_model": summary.get("ai_model"),
            "content_hash": summary.get("content_hash"),
            "created_at": summary.get("createdAt"),
            "updated_at": summary.get("updatedAt"),
        }
    else:
        return {"message": "not found"}
