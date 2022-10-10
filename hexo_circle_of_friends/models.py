# -*- coding:utf-8 -*-
# Author：yyyz
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BOOLEAN, DateTime, TEXT
from datetime import datetime, timedelta

Model = declarative_base()


class AbstractBase(Model):
    __abstract__ = True

    def to_dict(self):
        model_dict = dict(self.__dict__)
        del model_dict['_sa_instance_state']
        return model_dict


class Friend(AbstractBase):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256))
    link = Column(String(1024))
    avatar = Column(String(1024))
    error = Column(BOOLEAN)
    createAt = Column(DateTime, default=datetime.utcnow() + timedelta(hours=8))


class Post(AbstractBase):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256))
    created = Column(String(256))
    updated = Column(String(256))
    link = Column(String(1024))
    author = Column(String(256))
    avatar = Column(String(1024))
    rule = Column(String(256))
    createAt = Column(DateTime, default=datetime.utcnow() + timedelta(hours=8))


class Auth(AbstractBase):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True, autoincrement=True)
    password = Column(String(1024))


class Secret(AbstractBase):
    __tablename__ = 'secret'
    id = Column(Integer, primary_key=True, autoincrement=True)
    secret_key = Column(String(1024))
