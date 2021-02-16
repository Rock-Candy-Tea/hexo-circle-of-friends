# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import datetime
from operator import itemgetter
import leancloud
import sys
import re


def main():
        # 时间查找(中文、标准）
        def time_zero_plus(str):
            if len(str) < 2:
                str = '0' + str
            return str
        def find_time(str):
            try:
                timere_ch = re.compile(r'[0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日', re.S)
                time_ch = re.findall(timere_ch, str)[0]
                print('找到中文时间', time_ch)
                year = time_ch.split('年')[0].strip()
                month = time_zero_plus(time_ch.split('年')[1].split('月')[0].strip())
                day = time_zero_plus(time_ch.split('年')[1].split('月')[1].split('日')[0].strip())
                time = year + '-' + month + '-' + day
                print('获得标准时间', time)
            except:
                try:
                    timere = re.compile(r'[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}', re.S)
                    time = re.findall(timere, str)[0]
                    timelist = time.split('-')
                    time = timelist[0] + '-' + time_zero_plus(timelist[1]) + '-' + time_zero_plus(timelist[2])

                    print('获得标准时间', time)
                except:
                    print('没找到符合要求的时间')
            return time

        # 文章去重
        def delete_same_article(orign_friend_postpoor):
            friend_postpoor = []
            friend_poortitle = []
            for item in orign_friend_postpoor:
                if item['title'] not in friend_poortitle:
                    friend_poortitle.append(item['title'])
                    friend_postpoor.append(item)
                else:
                    print('-----------------')
                    print('重复1篇文章标题，已删除')
                    print('-----------------')
            return  friend_postpoor

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
            return  friend_poordic

        # gitee适配
        def reg(info_list, user_info, source):
            print('----')
            for item in info_list:
                reg = re.compile('(?<=' + item + ': ).*')
                result = re.findall(reg, str(source))
                result = result[0].replace('\r', ' ')
                print(result)
                user_info.append(result)

        # 从gitee获取friendlink
        def kang_api(friend_poor):
            print('\n')
            print('-------获取gitee友链----------')
            baselink = 'https://gitee.com'
            errortimes = 0
            f = open('userinfo.txt')
            git_info_list = ['owner', 'repo', 'state']
            user_info_txt = []
            info = f.read()
            reg(git_info_list, user_info_txt, info)
            print(user_info_txt)
            try:
                for number in range(1, 100):
                    print(number)
                    gitee = get_data('https://gitee.com/' +
                                     user_info_txt[0] +
                                     '/' +
                                     user_info_txt[1] +
                                     '/issues?state=' + user_info_txt[2] + '&page=' + str(number))
                    soup = BeautifulSoup(gitee, 'html.parser')
                    main_content = soup.find_all(id='git-issues')
                    linklist = main_content[0].find_all('a', {'class': 'title'})
                    if len(linklist) == 0:
                        print('爬取完毕')
                        print('失败了%r次' % errortimes)
                        break
                    for item in linklist:
                        issueslink = baselink + item['href']
                        issues_page = get_data(issueslink)
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
        # 全部删除
        def deleteall():
            Friendlist = leancloud.Object.extend('friend_list')

            def query_leancloud():
                try:
                    # 查询已有的数据
                    query = Friendlist.query
                    # 为查询创建别名
                    query.select('frindname', 'friendlink', 'firendimg', 'error')
                    # 选择类
                    query.limit(1000)
                    # 限定数量
                    query_list = query.find()
                except Exception as e:
                    print(e)
                    query_list = []
                return query_list

            query_list = query_leancloud()
            for query_j in query_list:
                delete = Friendlist.create_without_data(query_j.get('objectId'))
                delete.destroy()

        # 过期文章删除
        def outdate(query_list, Friendspoor, days):
            print('\n')
            print('-------执行过期删除规则----------')
            print('\n')
            out_date_post = 0
            for query_i in query_list:
                time = query_i.get('time')
                try:
                    query_time = datetime.datetime.strptime(time, "%Y-%m-%d")
                    if (today - query_time).days > days:
                        delete = Friendspoor.create_without_data(query_i.get('objectId'))
                        out_date_post += 1
                        delete.destroy()
                except Exception as e:
                    delete = Friendspoor.create_without_data(query_i.get('objectId'))
                    delete.destroy()
                    out_date_post += 1
                    print(e)
            print('\n')
            print('共删除了%s篇文章' % out_date_post)
            print('\n')
            print('-------结束删除规则----------')


        # leancloud数据  用户信息存储
        def leancloud_push_userinfo(friend_poordic):
            Friendlist = leancloud.Object.extend('friend_list')

            # 清除上一次数据
            deleteall()
            print('\n')
            print('-------清空友链列表----------')
            print('\n')

            # 定义查询函数
            def query_leancloud():
                try:
                    # 查询已有的数据
                    query = Friendlist.query
                    # 为查询创建别名
                    query.select('frindname', 'friendlink', 'firendimg', 'error')
                    # 选择类
                    query.limit(1000)
                    # 限定数量
                    query_list = query.find()
                except Exception as e:
                    print(e)
                    query_list = []
                return query_list

            # 查询
            query_list = query_leancloud()

            # 重复审查
            def repeat(name):
                upload = 'true'
                for query_item in query_list:
                    title = query_item.get('title')
                    if name == title:
                        upload = 'false'
                return upload

            # 数据上传
            for index, item in enumerate(friend_poordic):
                friendpoor = Friendlist()
                friendpoor.set('frindname', item[0])
                friendpoor.set('friendlink', item[1])
                friendpoor.set('firendimg', item[2])
                friendpoor.set('error', item[3])
                upload = repeat(item[0])
                if upload == 'true':
                    try:
                        friendpoor.save()
                    except Exception as e:
                        print(e)
                        friendpoor.save()
                    print("已上传第%s" % str(index + 1))
                else:
                    print("已上传第%s，但友链重复了" % str(index + 1))

        # leancloud数据  文章存储
        def leancloud_push(post_poor):

            # 声明class
            Friendspoor = leancloud.Object.extend('friend_poor')

            # 定义查询函数
            def query_leancloud():
                try:
                    # 查询已有的数据
                    query = Friendspoor.query
                    # 为查询创建别名
                    query.select('title', 'time', 'link')
                    # 选择类
                    query.limit(1000)
                    # 限定数量
                    query_list = query.find()
                except Exception as e:
                    print(e)
                    query_list = []
                return query_list

            # 查询
            query_list = query_leancloud()

            # 重复审查
            def repeat(name):
                upload = 'true'
                for query_item in query_list:
                    title = query_item.get('title')
                    if name == title:
                        upload = 'false'
                return upload

            # 数据上传
            for index, item in enumerate(post_poor):
                friendpoor = Friendspoor()
                friendpoor.set('title', item['title'])
                friendpoor.set('time', item['time'])
                friendpoor.set('link', item['link'])
                friendpoor.set('author', item['name'])
                friendpoor.set('headimg', item['img'])
                upload = repeat(item['title'])
                if upload == 'true':
                    try:
                        friendpoor.save()
                    except Exception as e:
                        print(e)
                        friendpoor.save()
                    print("已上传第%s" % str(index + 1))
                else:
                    print("已上传第%s，该文章名称重复不予上传" % str(index + 1))
            query_list = query_leancloud()
            outdate(query_list, Friendspoor, time_limit)

        # 请求连接
        def get_data(link):
            try:
                r = requests.get(link, timeout=15)
                r.encoding = 'utf-8-sig'
                result = r.text
            except:
                print('请求超过15s。')
            return result

        # 通过sitemap请求
        def sitmap_get(user_info):
            print('\n')
            print('-------执行sitemap规则----------')
            print('执行链接：', user_info[1])
            link = user_info[1]
            error_sitmap = 'false'
            try:
                result = get_data(link + '/sitemap.xml')
                soup = BeautifulSoup(result, 'html.parser')
                loc = soup.find_all('loc')
                if len(loc) == 0:
                    error_sitmap = 'true'
                    print('该网站可能没有sitemap')
                new_loc = []

                for loc_item in loc:
                    if 'index' in loc_item.text:
                        pass
                    elif loc_item.text.count('/') < 4:
                        pass
                    else:
                        new_loc.append(loc_item)
                print('该网站最新的五条sitemap为：',new_loc[0:5])
                if len(new_loc) != 0:
                    for i, new_loc_item in enumerate(new_loc[0:5]):
                        post_link = new_loc_item.text
                        result = get_data(post_link)
                        try:
                            time = find_time(str(result))
                            soup = BeautifulSoup(result, 'html.parser')
                            title = soup.find('title')
                            strtitle = title.text
                            titlesplit = strtitle.split("|", 1)
                            strtitle = titlesplit[0].strip()
                            post_info = {
                                'title': strtitle,
                                'time': time,
                                'link': post_link,
                                'name': user_info[0],
                                'img': user_info[2]
                            }
                            print(strtitle)
                            print(time)
                            print(post_link)
                            post_poor.append(post_info)
                            print("-----------获取到匹配结果----------")
                        except:
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
            return error_sitmap

        # 从主页获取文章
        def get_last_post(user_info):
            error_sitmap = 'false'
            link = user_info[1]
            print('\n')
            print('-------执行主页规则----------')
            print('执行链接：', link)
            result = get_data(link)
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
                        print(a.text)
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
            print("-----------结束主页规则----------")
            print('\n')
            return error_sitmap

        # 主方法获取友链池

        # 引入leancloud验证
        leancloud.init(sys.argv[1], sys.argv[2])
        friendpage_link = sys.argv[3]

        # 执行主方法
        print('----------------------')
        print('-----------！！开始执行爬取文章任务！！----------')
        print('----------------------')
        print('\n')
        today = datetime.datetime.today()
        time_limit = 60
        result = get_data(friendpage_link)
        soup = BeautifulSoup(result, 'html.parser')
        main_content = soup.find_all(id='article-container')
        link_list = main_content[0].find_all('a')
        friend_poor = []
        post_poor = []
        print('----------------------')
        print('-----------！！开始执行友链获取任务！！----------')
        print('----------------------')
        try:
            kang_api(friend_poor)
        except:
            print('读取gitee友链失败')
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
                    img = imglist[1].get('data-lazy-src')
                else:
                    imglist = item.find_all('img')
                    img = imglist[0].get('data-lazy-src')
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
        friend_poor = delete_same_link(friend_poor)
        print('当前友链数量',len( friend_poor))
        print('----------------------')
        print('-----------！！结束友链获取任务！！----------')
        print('----------------------')
        total_count = 0
        error_count = 0
        for index, item in enumerate(friend_poor):
            error = 'false'
            try:
                total_count += 1
                error = get_last_post(item)
                if error == 'true':
                    print("-----------获取主页信息失败，采取sitemap策略----------")
                    error = sitmap_get(item)
            except Exception as e:
                print('\n')
                print(item, "运用主页及sitemap爬虫爬取失败！请检查")
                print('\n')
                print(e)
                error_count += 1
            item.append(error)
        print('\n')
        print('----------------------')
        print("一共进行%s次" % total_count)
        print("一共失败%s次" % error_count)
        print('----------------------')
        print('\n')
        print('----------------------')
        print('-----------！！执行用户信息上传！！----------')
        print('----------------------')
        leancloud_push_userinfo(friend_poor)
        print('----------------------')
        print('-----------！！用户信息上传完毕！！----------')
        print('----------------------')
        post_poor.sort(key=itemgetter('time'), reverse=True)
        print('----------------------')
        print('-----------！！执行文章信息上传！！----------')
        print('----------------------')
        leancloud_push(post_poor)
        print('----------------------')
        print('-----------！！文章信息上传完毕！！----------')
        print('----------------------')


main()
