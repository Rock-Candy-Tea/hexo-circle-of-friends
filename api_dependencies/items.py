from typing import Union, Dict, List
from pydantic import BaseModel


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
    LINK: Union[List[Link], None] = None
    SETTINGS_FRIENDS_LINKS: Union[SettingsFriendsLinks, None] = None
    GITEE_FRIENDS_LINKS: Union[GitFriendsLinks, None] = None
    GITHUB_FRIENDS_LINKS: Union[GitFriendsLinks, None] = None
    BLOCK_SITE: Union[List[str], None] = None
    HTTP_PROXY: Union[bool, None] = None
    OUTDATE_CLEAN: Union[int, None] = None
    DATABASE: Union[str, None] = None
    DEPLOY_TYPE: Union[str, None] = None
