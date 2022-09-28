# -*- coding:utf-8 -*-
# Author：yyyz
import os
from hexo_circle_of_friends.utils.project import get_user_settings


def is_vercel_sqlite():
    settings = get_user_settings()
    return os.environ.get("VERCEL") and settings["DATABASE"] == "sqlite"


def is_vercel():
    return os.environ.get("VERCEL")
