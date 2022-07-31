# -*- coding:utf-8 -*-
# Author：yyyz

from typing import Union
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: Union[str, None] = None
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

if __name__ == '__main__':
    uvicorn.run("api.test.post:app", host="0.0.0.0",reload=True)