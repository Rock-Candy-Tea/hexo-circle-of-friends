# -*- coding:utf-8 -*-
# Author：yyyz
import asyncio

import aiohttp
from bs4 import BeautifulSoup

urls = []
domain = "https://github.com/"
new_li = []
async def fetch(session, url):
    async with session.get(url, verify_ssl=False) as response:
        content = await response.text()
        soup = BeautifulSoup(content, 'lxml')
        tag = soup.find("div", id="readme")
        if tag.find("g-emoji"):
            print(url)
            new_li.append(url)


async def main():
    async with aiohttp.ClientSession() as session:
        starturl = "https://github.com/Rock-Candy-Tea/hexo-circle-of-friends/network/members"
        async with session.get(starturl, verify_ssl=False) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'lxml')
            divs = soup.find_all("div", class_="repo")
            for div in divs:
                a = div.find_next("span").find_next_sibling("a")
                suffix = a.get("href")
                suffix = suffix.lstrip("/") if suffix.startswith("/") else ...
                url = domain + suffix
                urls.append(url)
            if urls:
                tasks = [asyncio.create_task(fetch(session, url)) for url in urls]
                await asyncio.wait(tasks)
        print(len(new_li))

if __name__ == '__main__':
    # find users who are using fc-version 4.3+
    asyncio.run(main())

