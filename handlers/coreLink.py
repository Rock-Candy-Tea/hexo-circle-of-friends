#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
友链处理 控件
"""
from bs4 import BeautifulSoup
import re

from handlers.coreSettings import configs as config
from request_data import request
from component.getTime import find_time
# 兼容
from component.ohter import *


# 友链链接去重
def delete_same_link(orign_friend_poordic):
    friend_poordic = []
    friend_poorlink = []
    for item in orign_friend_poordic:
        if item[1] not in friend_poorlink:
            friend_poorlink.append(item[1])
            friend_poordic.append(item)
        else:
            print('-----------------')
            print('重复1条友链链接，已删除')
            print('-----------------')
    return friend_poordic


# 链接屏蔽
def block_link(orign_friend_poordic):
    friend_poordic = []
    for item in orign_friend_poordic:
        if item[1] not in config.BLOCK_SITE:
            friend_poordic.append(item)
        else:
            print('-----------------')
            print('屏蔽1条友链链接，屏蔽链接为：', item[1])
            print('-----------------')
    return friend_poordic


# gitee适配
def reg(info_list, user_info, source):
    print('----')
    for item in info_list:
        reg = re.compile('(?<=' + item + ': ).*')
        result = re.findall(reg, str(source))
        result = result[0].replace('\r', '')
        print(result)
        user_info.append(result)


# 从github获取friendlink
def github_issuse(friend_poor, config=None):
    print('\n')
    print('-------获取github友链----------')
    baselink = 'https://github.com/'
    errortimes = 0
    config = config.yml
    print('owner:', config['setting']['github_friends_links']['owner'])
    print('repo:', config['setting']['github_friends_links']['repo'])
    print('state:', config['setting']['github_friends_links']['state'])
    try:
        for number in range(1, 100):
            print(number)
            github = request.get_data('https://github.com/' +
                                      config['setting']['github_friends_links']['owner'] +
                                      '/' +
                                      config['setting']['github_friends_links']['repo'] +
                                      '/issues?q=is%3A' + config['setting']['github_friends_links'][
                                          'state'] + '&page=' + str(number))
            soup = BeautifulSoup(github, 'html.parser')
            main_content = soup.find_all('div', {'aria-label': 'Issues'})
            linklist = main_content[0].find_all('a', {'class': 'Link--primary'})
            if len(linklist) == 0:
                print('爬取完毕')
                print('失败了%r次' % errortimes)
                break
            for item in linklist:
                issueslink = baselink + item['href']
                issues_page = request.get_data(issueslink)
                issues_soup = BeautifulSoup(issues_page, 'html.parser')
                try:
                    issues_linklist = issues_soup.find_all('pre')
                    source = issues_linklist[0].text
                    user_info = []
                    info_list = ['name', 'link', 'avatar']
                    reg(info_list, user_info, source)
                    if user_info[1] != '你的链接':
                        friend_poor.append(user_info)
                except:
                    errortimes += 1
                    continue
    except Exception as e:
        print('爬取完毕', e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)

    print('------结束github友链获取----------')
    print('\n')


# 从gitee获取friendlink
def kang_api(friend_poor):
    print('\n')
    print('-------获取gitee友链----------')
    baselink = 'https://gitee.com'
    errortimes = 0
    print('owner:', config['setting']['gitee_friends_links']['owner'])
    print('repo:', config['setting']['gitee_friends_links']['repo'])
    print('state:', config['setting']['gitee_friends_links']['state'])
    try:
        for number in range(1, 100):
            print(number)
            gitee = request.get_data('https://gitee.com/' +
                                     config['setting']['gitee_friends_links']['owner'] +
                                     '/' +
                                     config['setting']['gitee_friends_links']['repo'] +
                                     '/issues?state=' + config['setting']['gitee_friends_links'][
                                         'state'] + '&page=' + str(number))
            soup = BeautifulSoup(gitee, 'html.parser')
            main_content = soup.find_all(id='git-issues')
            linklist = main_content[0].find_all('a', {'class': 'title'})
            if len(linklist) == 0:
                print('爬取完毕')
                print('失败了%r次' % errortimes)
                break
            for item in linklist:
                issueslink = baselink + item['href']
                issues_page = request.get_data(issueslink)
                issues_soup = BeautifulSoup(issues_page, 'html.parser')
                try:
                    issues_linklist = issues_soup.find_all('code')
                    source = issues_linklist[0].text
                    user_info = []
                    info_list = ['name', 'link', 'avatar']
                    reg(info_list, user_info, source)
                    print(user_info)
                    if user_info[1] != '你的链接':
                        friend_poor.append(user_info)
                except:
                    errortimes += 1
                    continue
    except Exception as e:
        print('爬取完毕', e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)

    print('------结束gitee友链获取----------')
    print('\n')


# 请求连接
# 通过sitemap请求
def sitmap_get(user_info, post_poor, config=config.yml):
    print('\n')
    print('-------执行sitemap规则----------')
    print('执行链接：', user_info[1])
    link = user_info[1]
    error_sitmap = 'false'
    try:
        result = request.get_data(link + '/sitemap.xml')
        soup = BeautifulSoup(result, 'html.parser')
        url = soup.find_all('url')
        if len(url) == 0:
            result = request.get_data(link + '/baidusitemap.xml')
            soup = BeautifulSoup(result, 'html.parser')
            url = soup.find_all('url')
        new_link_list = []
        for item in url:
            box = []
            url_link = item.find('loc')
            url_date = item.find('lastmod')
            box.append(url_link)
            box.append(url_date)
            new_link_list.append(box)

        def takeSecond(elem):
            return str(elem[1])[9:19]

        new_link_list.sort(key=takeSecond, reverse=True)
        if len(url) == 0:
            error_sitmap = 'true'
            print('该网站可能没有sitemap')
        block_word = config['setting']['block_word']
        new_loc = []
        new_loc_time = []
        for item in new_link_list:
            loc_item = item[0]
            time = item[1]
            if loc_item.text[-1] == '/':
                limit_number = 5
            else:
                limit_number = 4
            block = False
            for item in block_word:
                if item in loc_item.text:
                    block = True
            if block:
                pass
            elif loc_item.text.count('/') < limit_number:
                pass
            else:
                new_loc.append(loc_item)
                new_loc_time.append(time)
        if len(new_loc) < 1:
            for item in new_link_list:
                loc_item = item[0]
                time = item[1]
                if loc_item.text[-1] == '/':
                    limit_number = 3
                else:
                    limit_number = 2
                block = False
                for item in block_word:
                    if item in loc_item.text:
                        block = True
                if block:
                    pass
                elif loc_item.text.count('/') == limit_number:
                    pass
                else:
                    new_loc.append(loc_item)
                    new_loc_time.append(time)
        print('该网站最新的五条sitemap为：', new_loc[0:5])
        print('该网站最新的五个时间戳为：', new_loc_time[0:5])
        print('-------开始详情页面爬取----------')
        if len(new_loc) != 0:
            for i, new_loc_item in enumerate(new_loc[0:5]):
                post_link = new_loc_item.text
                result = request.get_data(post_link)
                if result == 'error':
                    continue
                try:
                    time = find_time(str(result))
                    if time == '':
                        time = str(new_loc_time[i])[9:19]
                        print('采用sitemap时间', time)
                    soup = BeautifulSoup(result, 'html.parser')
                    title = soup.find('title')
                    strtitle = title.text
                    block_chars = config['setting']['block_chars']
                    for item in block_chars:
                        titlesplit = strtitle.split(item, 1)
                        strtitle = titlesplit[0].strip()
                    post_info = {
                        'title': strtitle,
                        'time': time,
                        'link': post_link,
                        'name': user_info[0],
                        'img': user_info[2]
                    }
                    print(strtitle.encode("gbk", 'ignore').decode('gbk', 'ignore'))
                    print(time)
                    print(post_link)
                    post_poor.append(post_info)
                    print("-----------获取到匹配结果----------")
                except Exception as e:
                    print(e)
                    print(e.__traceback__.tb_frame.f_globals["__file__"])
                    print(e.__traceback__.tb_lineno)
                    print('网站不包含规范的时间格式！')
                    error_sitmap = 'true'
    except Exception as e:
        print('无法请求sitemap')
        print(e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)
        error_sitmap = 'true'
    print('-----------结束sitemap规则----------')
    print('\n')
    return error_sitmap, post_poor