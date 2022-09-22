from typing import Union
from pydantic import BaseModel


class PassWord(BaseModel):
    password: str

class Admin(BaseModel):
    pass

class Guest(BaseModel):
    pass

