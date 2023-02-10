import os
from typing import Optional, List
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
    MAX_POSTS_NUM: int = get_user_settings()["MAX_POSTS_NUM"]
    HTTP_PROXY: bool = get_user_settings()["HTTP_PROXY"]
    OUTDATE_CLEAN: int = get_user_settings()["OUTDATE_CLEAN"]
    DATABASE: str = get_user_settings()["DATABASE"]
    DEPLOY_TYPE: str = get_user_settings()["DEPLOY_TYPE"]


class FcBaseEnv(BaseModel):
    PROXY: Optional[str] = os.environ.get("PROXY")
    APPID: Optional[str] = os.environ.get("APPID")
    APPKEY: Optional[str] = os.environ.get("APPKEY")
    MYSQL_USERNAME: Optional[str] = os.environ.get("MYSQL_USERNAME")
    MYSQL_PASSWORD: Optional[str] = os.environ.get("MYSQL_PASSWORD")
    MYSQL_IP: Optional[str] = os.environ.get("MYSQL_IP")
    MYSQL_PORT: Optional[int] = os.environ.get("MYSQL_PORT")
    MYSQL_DB: Optional[str] = os.environ.get("MYSQL_DB")
    GH_NAME: Optional[str] = os.environ.get("GH_NAME")
    GH_EMAIL: Optional[str] = os.environ.get("GH_EMAIL")
    GH_TOKEN: Optional[str] = os.environ.get("GH_TOKEN")
    MONGODB_URI: Optional[str] = os.environ.get("MONGODB_URI")


class GitHubEnv(FcBaseEnv):
    STORAGE_TYPE: str = get_user_settings()["DATABASE"]

    @validator('STORAGE_TYPE')
    def storage_name_must_contain(cls, v):
        if v not in ["leancloud", "sqlite", "mysql", "mongodb"]:
            raise ValueError('存储方式必须为其中一个：leancloud,sqlite,mysql,mongodb')
        return v


class VercelEnv(FcBaseEnv):
    VERCEL_ACCESS_TOKEN: str = os.environ.get("VERCEL_ACCESS_TOKEN", "")


class ServerEnv(FcBaseEnv):
    EXPOSE_PORT: int = os.environ["EXPOSE_PORT"] if os.environ.get("EXPOSE_PORT") else 8000
    RUN_PER_HOURS: int = os.environ["RUN_PER_HOURS"] if os.environ.get("RUN_PER_HOURS") else 6
