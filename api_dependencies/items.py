from typing import Union, Dict, List
from pydantic import BaseModel
from hexo_circle_of_friends.utils.project import get_base_path
import yaml
import os

base_path = get_base_path()
try:
    path = os.path.join(base_path, "hexo_circle_of_friends/fc_settings.yaml")
    with open(path, "r", encoding="utf-8") as f:
        user_conf = yaml.safe_load(f)
except:
    raise IOError


class PassWord(BaseModel):
    password: str


class Link(BaseModel):
    link: str
    theme: str


class SettingsFriendsLinks(BaseModel):
    enable: bool
    json_api: str
    list: List[List[str]]


class GitFriendsLinks(BaseModel):
    enable: bool
    type: str
    owner: str
    repo: str
    state: str


class FcSettings(BaseModel):
    LINK: List[Link] = user_conf["LINK"]
    SETTINGS_FRIENDS_LINKS: SettingsFriendsLinks = user_conf["SETTINGS_FRIENDS_LINKS"]
    GITEE_FRIENDS_LINKS: GitFriendsLinks = user_conf["GITEE_FRIENDS_LINKS"]
    GITHUB_FRIENDS_LINKS: GitFriendsLinks = user_conf["GITHUB_FRIENDS_LINKS"]
    BLOCK_SITE: List[str] = user_conf["BLOCK_SITE"]
    HTTP_PROXY: bool = user_conf["HTTP_PROXY"]
    OUTDATE_CLEAN: int = user_conf["OUTDATE_CLEAN"]
    DATABASE: str = user_conf["DATABASE"]
    DEPLOY_TYPE: str = user_conf["DEPLOY_TYPE"]
