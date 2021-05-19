  # -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import datetime
from request_data import request

# sakura 友链规则
def get_friendlink(friendpage_link, friend_poor):
    result = request.get_data(friendpage_link)
    soup = BeautifulSoup(result, 'html.parser')
    main_content = soup.find_all('li', {"class": "link-item"})
    for item in main_content:
        img = item.find('img').get('data-src')
        link = item.find('a').get('href')
        name = item.find('span').text
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

# 从sakura主页获取文章
def get_last_post(user_info,post_poor):
            error_sitmap = False
            link = user_info[1]
            print('\n')
            print('-------执行sakura主页规则----------')
            print('执行链接：', link)
            result = request.get_data(link)
            soup = BeautifulSoup(result, 'html.parser')
            main_content = soup.find_all(id='main')
            time_excit = soup.find_all('div',{"class": "post-date"})
            if main_content and time_excit:
                error_sitmap = True
                link_list = main_content[0].find_all('div', {"class": "post-date"})
                lasttime = datetime.datetime.strptime('1970-01-01', "%Y-%m-%d")
                for index, item in enumerate(link_list):
                    time = item.text
                    time = time.replace("|","")
                    time = time.replace(" ", "")
                    time = time.replace("\n", "")
                    time = time.replace("发布于", "")
                    time = time.replace("\t", "")

                    if lasttime < datetime.datetime.strptime(time, "%Y-%m-%d"):
                        lasttime = datetime.datetime.strptime(time, "%Y-%m-%d")
                lasttime = lasttime.strftime('%Y-%m-%d')
                print('最新时间是', lasttime)
                last_post_list = main_content[0].find_all('article', {"class": "post"})
                for item in last_post_list:
                    time_created = item.find('div', {"class": "post-date"}).text.strip()
                    time_created = time_created.replace(" ", "")
                    time_created = time_created.replace("发布于", "")
                    time_created = time_created.replace("\t", "")
                    if time_created == lasttime:
                        error_sitmap = False
                        print(lasttime)
                        a = item.find('a')
                        # print(item.find('a'))
                        alink = a['href']
                        alinksplit = alink.split("/", 1)
                        stralink = alinksplit[1].strip()
                        if link[-1] != '/':
                            link = link + '/'
                        print(item.find('h3').text.strip().encode("gbk", 'ignore').decode('gbk', 'ignore'))
                        link = link.split('/')[0]
                        print(link + '/' + stralink)
                        print("-----------获取到匹配结果----------")
                        post_info = {
                            'title': item.find('h3').text.strip(),
                            'time': lasttime,
                            'link': link + '/' + stralink,
                            'name': user_info[0],
                            'img': user_info[2]
                        }
                        post_poor.append(post_info)
            else:
                error_sitmap = True
                print('貌似不是类似sakura主题！')
            print("-----------结束sakura主页规则----------")
            print('\n')
            return error_sitmap