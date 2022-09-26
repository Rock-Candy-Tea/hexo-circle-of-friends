# -*- coding:utf-8 -*-
# Author：yyyz

from typing import Union,List
import uvicorn
from fastapi import FastAPI, Query, Body
from pydantic import BaseModel, Field,HttpUrl


class Item(BaseModel):
    name: str
    description: Union[str, None] = Field(default=None, max_length=15, min_length=3)
    price: float
    tax: Union[float, None] = None


app = FastAPI()


@app.post("/items")
async def create_item(item: Item):
    print(item)
    print(item.name)
    print(item.price)
    print(item.tax)

    return item

class Image(BaseModel):
    url: HttpUrl
    name: str


@app.post("/images/multiple/")
async def create_multiple_images(images: List[Image]):
    return images

if __name__ == '__main__':
    uvicorn.run("api.test.post:app", host="0.0.0.0", reload=True)
