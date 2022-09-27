from typing import Union, Dict, List
from pydantic import BaseModel, validator
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


class FcEnv(BaseModel):
    PROXY: Union[str, None] = None
    APPID: Union[str, None] = None
    APPKEY: Union[str, None] = None
    MYSQL_USERNAME: Union[str, None] = None
    MYSQL_PASSWORD: Union[str, None] = None
    MYSQL_IP: Union[str, None] = None
    MYSQL_PORT: Union[int, None] = None
    MYSQL_DB: Union[str, None] = None
    GITHUB_NAME: Union[str, None] = None
    GITHUB_EMAIL: Union[str, None] = None
    GITHUB_TOKEN: Union[str, None] = None
    MONGODB_URI: Union[str, None] = None
    STORAGE_TYPE: str = "leancloud"
    EXPOSE_PORT: int = 8000
    RUN_PER_HOURS: int = 6

    @validator('STORAGE_TYPE')
    def storage_name_must_contain(cls, v):
        if v not in ["leancloud", "sqlite", "mysql", "mongodb"]:
            raise ValueError('存储方式必须为其中一个：leancloud,sqlite,mysql,mongodb')
        return v
