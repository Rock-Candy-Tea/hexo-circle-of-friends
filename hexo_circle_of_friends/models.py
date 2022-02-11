# -*- coding:utf-8 -*-
# Author：yyyz
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BOOLEAN, DateTime
from datetime import datetime,timedelta

Model = declarative_base()


class Friend(Model):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256))
    link = Column(String(1024))
    avatar = Column(String(1024))
    error = Column(BOOLEAN)
    createAt = Column(DateTime, default=datetime.now() + timedelta(hours=8))


class Post(Model):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256))
    created = Column(String(256))
    updated = Column(String(256))
    link = Column(String(1024))
    author = Column(String(256))
    avatar = Column(String(1024))
    rule = Column(String(256))
    createAt = Column(DateTime, default=datetime.now() + timedelta(hours=8))
