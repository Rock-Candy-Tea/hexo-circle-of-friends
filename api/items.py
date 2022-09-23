from typing import Union, Dict, List
from pydantic import BaseModel


class PassWord(BaseModel):
    password: str


class FcSettings(BaseModel):
    # LINK: Dict[str:str]
    # SETTINGS_FRIENDS_LINKS: Dict[str:Union[bool, str, List[List[str]]]]
    # GITEE_FRIENDS_LINKS: Dict[str:str]
    # GITHUB_FRIENDS_LINKS: Dict[str:str]
    # BLOCK_SITE: List[str]
    # HTTP_PROXY: bool
    # OUTDATE_CLEAN: int
    DATABASE: str
    DEPLOY_TYPE: str
