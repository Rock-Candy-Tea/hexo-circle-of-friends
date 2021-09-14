#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
友链处理 控件
"""
from bs4 import BeautifulSoup
import re

from handlers.coreSettings import configs as config
from component import getWeb as request
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
            # print('-----------------')
            print('友链重复，已删除！链接为：', item[1])
            # print('-----------------')
    return friend_poordic


# 链接屏蔽
def block_link(orign_friend_poordic, config = config.yml):
    from handlers.coreSettings import configs
    friend_poordic = []
    # block_site = config['setting']['block_site']
    block_site = configs.BLOCK_SITE
    for item in orign_friend_poordic:
        if item[1] not in block_site:
            friend_poordic.append(item)
        else:
            # print('-----------------')
            print('屏蔽1条友链链接，屏蔽链接为：', item[1])
            # print('-----------------')
    return friend_poordic


# gitee适配
def reg(info_list, user_info, source):
    # print('----')
    for item in info_list:
        reg = re.compile('(?<=' + item + ': ).*')
        result = re.findall(reg, str(source))
        result = result[0].replace('\r', '')
        # print(result)
        user_info.append(result)


# 从github获取friendlink
def github_issuse(friend_poor, config=None):
    # print('\n')
    # print('-------获取github友链----------')
    baselink = 'https://github.com/'
    errortimes = 0
    # config = config.yml
    # print('owner:', config['setting']['github_friends_links']['owner'])
    # print('repo:', config['setting']['github_friends_links']['repo'])
    # print('state:', config['setting']['github_friends_links']['state'])
    try:
        for number in range(1, 100):
            # print(number)
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
                # print('爬取完毕')
                # print('失败了%r次' % errortimes)
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
        pass
        # print('爬取完毕', e)
        # print(e.__traceback__.tb_frame.f_globals["__file__"])
        # print(e.__traceback__.tb_lineno)

    # print('------结束github友链获取----------')
    # print('\n')


# 从gitee获取friendlink
def kang_api(friend_poor, config=None):
    # print('\n')
    # print('-------获取gitee友链----------')
    baselink = 'https://gitee.com'
    errortimes = 0
    # config = config.yml
    # print('owner:', config['setting']['gitee_friends_links']['owner'])
    # print('repo:', config['setting']['gitee_friends_links']['repo'])
    # print('state:', config['setting']['gitee_friends_links']['state'])
    try:
        for number in range(1, 100):
            # print(number)
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
                # print('爬取完毕')
                # print('失败了%r次' % errortimes)
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
                    # print(user_info)
                    if user_info[1] != '你的链接':
                        friend_poor.append(user_info)
                except:
                    errortimes += 1
                    continue
    except Exception as e:
        pass
        # print('爬取完毕', e)
        # print(e.__traceback__.tb_frame.f_globals["__file__"])
        # print(e.__traceback__.tb_lineno)

    # print('------结束gitee友链获取----------')
    # print('\n')


# 从setting.py获取friendlink
def config_friendlink(friend_poor, config=None):
    from handlers.coreSettings import configs
    for user_info in configs.CONFIG_FRIENDS_LINKS['list']:
        print('----------------------')
        print('好友名%r' % user_info[0])
        print('头像链接%r' % user_info[2])
        print('主页链接%r' % user_info[1])
        friend_poor.append(user_info)


# 请求连接
# 通过sitemap请求（重写中...（我放弃了））
def sitmap_get(user_info, post_poor, config=config.yml):
    # print('\n')
    # print('-------执行sitemap规则----------')
    # print('执行链接：', user_info[1])
    link = user_info[1]
    error_sitmap = False
    try:
        result = request.get_data(link + '/sitemap.xml')
        soup = BeautifulSoup(result, 'html.parser')
        items = soup.find_all('url')
        if len(items) == 0:
            result = request.get_data(link + '/baidusitemap.xml')
            soup = BeautifulSoup(result, 'html.parser')
            items = soup.find_all('url')
        l = 5
        new_loc = []
        new_loc_time = []
        if len(items) < 5: l = len(items)
        if l == 0:
            error_sitmap = True
            # print('该网站可能没有rss')
        else:
            for i in range(l):
                post_info = {}
                item = items[i]
                
                # new_loc.append(url)
                # new_loc_time.append(time)
                # post_poor.append(post_info)
            # print('该网站最新的{}条rss为：'.format(l), new_loc[0:5])
            # print('该网站最新的{}个时间为：'.format(l), new_loc_time[0:5])
            
    except Exception as e:
        # print('无法请求sitemap')
        # print(e)
        # print(e.__traceback__.tb_frame.f_globals["__file__"])
        # print(e.__traceback__.tb_lineno)
        error_sitmap = True
    return error_sitmap, post_poor


# 通过atom请求
def atom_get(user_info, post_poor, config=config.yml):
    # print('\n')
    # print('-------执行atom规则----------')
    # print('执行链接：', user_info[1])
    link = user_info[1]
    error_atom = False
    try:
        html = request.get_data(link + "/atom.xml")
        # # print(html)
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all("entry")
        if len(items) == 0:
            html = request.get_data(link + "/feed/atom.xml")
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.find_all("entry")
        l = 5
        new_loc = []
        new_loc_time = []
        if len(items) < 5: l = len(items)

        if l == 0:
            error_atom = True
            # print('该网站可能没有atom')
        else:
            for i in range(l):
                post_info = {}
                item = items[i]
                title = item.find("title").text
                url = item.find("link")['href']
                time = item.find("published").text[:10]
                updated = item.find("updated").text[:10]
                post_info['title'] = title
                post_info['time'] = time
                post_info['updated'] = updated
                post_info['link'] = url
                post_info['name'] = user_info[0]
                post_info['img'] = user_info[2]
                post_info['rule'] = "atom"
                new_loc.append(url)
                new_loc_time.append(time)
                post_poor.append(post_info)
            # print('该网站最新的{}条atom为：'.format(l), new_loc[0:5])
            # print('该网站最新的{}个时间为：'.format(l), new_loc_time[0:5])
    except Exception as e:
        # print('无法请求atom')
        # print(e)
        # print(e.__traceback__.tb_frame.f_globals["__file__"])
        # print(e.__traceback__.tb_lineno)
        error_atom = True
    # print('-----------结束atom规则----------')
    # print('\n')
    return error_atom, post_poor


# 通过RSS2请求
def rss2_get(user_info, post_poor, config=config.yml):
    # print('\n')
    # print('-------执行rss2规则----------')
    # print('执行链接：', user_info[1])
    link = user_info[1]
    error_atom = False
    try:
        html = request.get_data(link + "/rss.xml")
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all("item")
        if len(items) == 0:
            html = request.get_data(link + "/rss2.xml")
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.find_all("item")
        l = 5
        new_loc = []
        new_loc_time = []
        if len(items) < 5: l = len(items)
        if l == 0:
            error_atom = True
            # print('该网站可能没有rss')
        else:
            for i in range(l):
                post_info = {}
                item = items[i]
                title = item.find("title").text
                url = item.find("link").text
                timedata = item.find("pubDate").text.split(" ")
                y, m, d = int(timedata[3]), list(calendar.month_abbr).index(timedata[2]), int(timedata[1])
                time = "{:02d}-{:02d}-{:02d}".format(y,m,d)
                post_info['title'] = title
                post_info['time'] = time
                post_info['updated'] = time
                post_info['link'] = url
                post_info['name'] = user_info[0]
                post_info['img'] = user_info[2]
                post_info['rule'] = "rss2"
                new_loc.append(url)
                new_loc_time.append(time)
                post_poor.append(post_info)
            # print('该网站最新的{}条rss为：'.format(l), new_loc[0:5])
            # print('该网站最新的{}个时间为：'.format(l), new_loc_time[0:5])
    except Exception as e:
        # print('无法请求rss/rss2')
        # print(e)
        # print(e.__traceback__.tb_frame.f_globals["__file__"])
        # print(e.__traceback__.tb_lineno)
        error_atom = True
    # print('-----------结束rss2规则----------')
    # print('\n')
    return error_atom, post_poor