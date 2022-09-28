import os
from typing import Union, Dict, List
from pydantic import BaseModel, validator
from hexo_circle_of_friends.utils.project import get_user_settings


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
    LINK: List[Link] = get_user_settings()["LINK"]
    SETTINGS_FRIENDS_LINKS: SettingsFriendsLinks = get_user_settings()["SETTINGS_FRIENDS_LINKS"]
    GITEE_FRIENDS_LINKS: GitFriendsLinks = get_user_settings()["GITEE_FRIENDS_LINKS"]
    GITHUB_FRIENDS_LINKS: GitFriendsLinks = get_user_settings()["GITHUB_FRIENDS_LINKS"]
    BLOCK_SITE: List[str] = get_user_settings()["BLOCK_SITE"]
    HTTP_PROXY: bool = get_user_settings()["HTTP_PROXY"]
    OUTDATE_CLEAN: int = get_user_settings()["OUTDATE_CLEAN"]
    DATABASE: str = get_user_settings()["DATABASE"]
    DEPLOY_TYPE: str = get_user_settings()["DEPLOY_TYPE"]


class FcBaseEnv(BaseModel):
    PROXY: Union[str, None] = None
    APPID: Union[str, None] = None
    APPKEY: Union[str, None] = None
    MYSQL_USERNAME: Union[str, None] = None
    MYSQL_PASSWORD: Union[str, None] = None
    MYSQL_IP: Union[str, None] = None
    MYSQL_PORT: Union[int, None] = None
    MYSQL_DB: Union[str, None] = None
    GH_NAME: Union[str, None] = None
    GH_EMAIL: Union[str, None] = None
    GH_TOKEN: Union[str, None] = None
    MONGODB_URI: Union[str, None] = None
    # STORAGE_TYPE: str = get_user_settings()["DATABASE"]
    # EXPOSE_PORT: int = 8000
    # RUN_PER_HOURS: int = 6


class GitHubEnv(FcBaseEnv):
    STORAGE_TYPE: str = get_user_settings()["DATABASE"]

    @validator('STORAGE_TYPE')
    def storage_name_must_contain(cls, v):
        if v not in ["leancloud", "sqlite", "mysql", "mongodb"]:
            raise ValueError('存储方式必须为其中一个：leancloud,sqlite,mysql,mongodb')
        return v


class VercelEnv(FcBaseEnv):
    VERCEL_ACCESS_TOKEN: str = os.environ.get("VERCEL_ACCESS_TOKEN", "")
