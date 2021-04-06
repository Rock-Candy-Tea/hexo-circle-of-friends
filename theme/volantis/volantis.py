# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import datetime
import yaml
from request_data import request

def load_config():
    f = open('_config.yml', 'r',encoding='utf-8')
    ystr = f.read()
    ymllist = yaml.load(ystr, Loader=yaml.FullLoader)
    return ymllist

def github_issuse(friend_poor):
    print('\n')
    print('-------获取volantis-github友链----------')
    baselink = 'https://github.com/'
    errortimes = 0
    config = load_config()
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
                             '/issues?q=is%3A' + config['setting']['github_friends_links']['state'] + '&page=' + str(number))
            soup = BeautifulSoup(github, 'html.parser')
            main_content = soup.find_all('div',{'aria-label': 'Issues'})
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
                    info_list = ['title', 'url', 'avatar']
                    reg_volantis(info_list, user_info, source)
                    if user_info[1] != '你的链接':
                        friend_poor.append(user_info)
                except:
                    errortimes += 1
                    continue
    except Exception as e:
        print('爬取完毕', e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)

    print('------结束volantis-github友链获取----------')
    print('\n')

# gitee适配
def reg(info_list, user_info, source):
    print('----')
    for item in info_list:
        reg = re.compile('(?<=' + item + ': ).*')
        result = re.findall(reg, str(source))
        result = result[0].replace('\r', '')
        print(result)
        user_info.append(result)


def reg_volantis(info_list, user_info, source):
    print('----')
    for item in info_list:
        reg = re.compile('(?<=' + item + '": ).*')
        result = re.findall(reg, str(source))
        result = result[0].replace('\r', '')
        result = result.replace('"', '')
        result = result.replace(',', '')
        print(result)
        user_info.append(result)


def gitee_issuse(friend_poor):
    print('\n')
    print('-------获取volantis-gitee友链----------')
    baselink = 'https://gitee.com'
    errortimes = 0
    config = load_config()
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
                             '/issues?state=' + config['setting']['gitee_friends_links']['state'] + '&page=' + str(number))
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
                    info_list = ['title', 'url', 'avatar']
                    reg_volantis(info_list, user_info, source)
                    if user_info[1] != '你的链接':
                        friend_poor.append(user_info)
                except:
                    errortimes += 1
                    continue
    except Exception as e:
        print('爬取完毕', e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)

    print('------结束volantis-gitee友链获取----------')
    print('\n')


# Volantis  友链规则
def volantis_get_friendlink(friendpage_link, friend_poor):
    main_content = []
    result = request.get_data(friendpage_link)
    soup = BeautifulSoup(result, 'html.parser')
    # Volantis sites
    if len(soup.find_all('a', {"class": "site-card"})) > 0:
        main_content = soup.find_all('a', {"class": "site-card"})
        print('使用Volantis simple')
    # Volantis simple
    elif len(soup.find_all('a', {"class": "simpleuser"})) > 0:
        main_content = soup.find_all('a', {"class": "simpleuser"})
        print('使用Volantis traditional')
    # Volantis traditional
    elif len(soup.find_all('a', {"class": "friend-card"})) > 0:
        main_content = soup.find_all('a', {"class": "friend-card"})
        print('使用Volantis sites')
    else:
        print('不包含标准volantis友链！')
    for item in main_content:
        if len(item.find_all('img')) > 1:
            img = item.find_all('img')[1].get('src')
        else:
            img = item.find('img').get('src')
        link = item.get('href')
        if item.find('span'):
            name = item.find('span').text
        elif item.find('p'):
            name = item.find('p').text
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
    config = load_config()
    if config['setting']['gitee_friends_links']['enable'] and config['setting']['gitee_friends_links']['type'] == 'volantis':
        gitee_issuse(friend_poor)
    if config['setting']['github_friends_links']['enable'] and config['setting']['github_friends_links']['type'] == 'volantis':
        github_issuse(friend_poor)


def get_last_post_from_volantis(user_info, post_poor):
    error_sitmap = 'false'
    link = user_info[1]
    print('\n')
    print('-------执行volantis主页规则----------')
    print('执行链接：', link)
    result = request.get_data(link)
    soup = BeautifulSoup(result, 'html.parser')
    main_content = soup.find_all('section', {"class": "post-list"})
    time_excit = soup.find_all('time')
    if main_content and time_excit:
        error_sitmap = 'true'
        link_list = main_content[0].find_all('time')
        lasttime = datetime.datetime.strptime('1970-01-01', "%Y-%m-%d")
        for index, item in enumerate(link_list):
            time = item.text
            time = time.replace("|", "")
            time = time.replace(" ", "")
            time = time.replace("\n", "")
            if lasttime < datetime.datetime.strptime(time, "%Y-%m-%d"):
                lasttime = datetime.datetime.strptime(time, "%Y-%m-%d")
        lasttime = lasttime.strftime('%Y-%m-%d')
        print('最新时间是', lasttime)
        last_post_list = main_content[0].find_all('div', {"class": "post-wrapper"})
        for item in last_post_list:
            if item.find('time'):
                time_created = item.find('time').text.strip()
            else:
                time_created = ''
            if time_created == lasttime:
                error_sitmap = 'false'
                print(lasttime)
                a = item.find('a')
                alink = a['href']
                alinksplit = alink.split("/", 1)
                stralink = alinksplit[1].strip()
                if link[-1] != '/':
                    link = link + '/'
                print(item.find('h2', {"class": "article-title"}).text.strip().encode("gbk", 'ignore').decode('gbk', 'ignore'))
                print(link + stralink)
                print("-----------获取到匹配结果----------")
                post_info = {
                    'title': item.find('h2', {"class": "article-title"}).text.strip(),
                    'time': lasttime,
                    'link': link + stralink,
                    'name': user_info[0],
                    'img': user_info[2]
                }
                post_poor.append(post_info)
    else:
        error_sitmap = 'true'
        print('貌似不是类似volantis主题！')
    print("-----------结束主页规则----------")
    print('\n')
    return error_sitmap
