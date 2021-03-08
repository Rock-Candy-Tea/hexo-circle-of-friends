# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import datetime
from request_data import request

# butterfly 友链规则
def butterfly_get_friendlink(friendpage_link, friend_poor):
    result = request.get_data(friendpage_link)
    soup = BeautifulSoup(result, 'html.parser')
    main_content = soup.find_all(id='article-container')
    link_list = main_content[0].find_all('a')
    for index, item in enumerate(link_list):
        link = item.get('href')
        if link.count('/') > 3:
            continue
        if item.get('title'):
            name = item.get('title')
        else:
            try:
                name = item.find('span').text
            except:
                continue
        try:
            if len(item.find_all('img')) > 1:
                imglist = item.find_all('img')
                if imglist[1].get('data-lazy-src'):
                    img = imglist[1].get('data-lazy-src')
                else:
                    img = imglist[1].get('src')
            else:
                imglist = item.find_all('img')
                if imglist[0].get('data-lazy-src'):
                    img = imglist[0].get('data-lazy-src')
                else:
                    img = imglist[0].get('src')
        except:
            continue
        if "#" in link:
            pass
        else:
            user_info = []
            user_info.append(name)
            user_info.append(link)
            user_info.append(img)
            print('----------------------')
            try:
                print('好友名%r' % name)
            except:
                print('非法用户名')
            print('头像链接%r' % img)
            print('主页链接%r' % link)
            friend_poor.append(user_info)

# 从butterfly主页获取文章
def get_last_post_from_butterfly(user_info,post_poor):
            error_sitmap = 'false'
            link = user_info[1]
            print('\n')
            print('-------执行butterfly主页规则----------')
            print('执行链接：', link)
            result = request.get_data(link)
            soup = BeautifulSoup(result, 'html.parser')
            main_content = soup.find_all(id='recent-posts')
            time_excit = soup.find_all('time')
            if main_content and time_excit:
                error_sitmap = 'true'
                link_list = main_content[0].find_all('time', {"class": "post-meta-date-created"})
                if link_list == []:
                    print('该页面无文章生成日期')
                    link_list = main_content[0].find_all('time')
                else:
                    print('该页面有文章生成日期')
                lasttime = datetime.datetime.strptime('1970-01-01', "%Y-%m-%d")
                for index, item in enumerate(link_list):
                    time = item.text
                    time = time.replace("|","")
                    time = time.replace(" ", "")
                    if lasttime < datetime.datetime.strptime(time, "%Y-%m-%d"):
                        lasttime = datetime.datetime.strptime(time, "%Y-%m-%d")
                lasttime = lasttime.strftime('%Y-%m-%d')
                print('最新时间是', lasttime)
                last_post_list = main_content[0].find_all('div', {"class": "recent-post-info"})
                for item in last_post_list:
                    time_created = item.find('time', {"class": "post-meta-date-created"})
                    if time_created:
                        pass
                    else:
                        time_created = item
                    if time_created.find(text=lasttime):
                        error_sitmap = 'false'
                        print(lasttime)
                        a = item.find('a')
                        # print(item.find('a'))
                        alink = a['href']
                        alinksplit = alink.split("/", 1)
                        stralink = alinksplit[1].strip()
                        if link[-1] != '/':
                            link = link + '/'
                        print(a.text.encode("gbk", 'ignore').decode('gbk', 'ignore'))
                        print(link + stralink)
                        print("-----------获取到匹配结果----------")
                        post_info = {
                            'title': a.text,
                            'time': lasttime,
                            'link': link + stralink,
                            'name': user_info[0],
                            'img': user_info[2]
                        }
                        post_poor.append(post_info)
            else:
                error_sitmap = 'true'
                print('貌似不是类似butterfly主题！')
            print("-----------结束butterfly主页规则----------")
            print('\n')
            return error_sitmap
