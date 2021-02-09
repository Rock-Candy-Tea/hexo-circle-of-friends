import requests
from bs4 import BeautifulSoup
import datetime
from operator import itemgetter
import leancloud
import sys



def main():
    # 全部删除
    def deleteall():
        Friendlist = leancloud.Object.extend('friend_list')
        def query_leancloud():
            try:
                # 查询已有的数据
                query = Friendlist.query
                # 为查询创建别名
                query.select('frindname','friendlink','firendimg','error')
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
        for query_i in query_list:
            time = query_i.get('time')
            try:
                query_time = datetime.datetime.strptime(time, "%Y-%m-%d")
                if (today - query_time).days > days:
                    delete = Friendspoor.create_without_data(query_i.get('objectId'))
                    delete.destroy()
            except Exception as e:
                delete = Friendspoor.create_without_data(query_i.get('objectId'))
                delete.destroy()
                print(e)

    # leancloud数据  用户信息存储
    def leancloud_push_userinfo(friend_poordic):
        Friendlist = leancloud.Object.extend('friend_list')

        # 清除上一次数据
        deleteall()

        # 定义查询函数
        def query_leancloud():
            try:
                # 查询已有的数据
                query = Friendlist.query
                # 为查询创建别名
                query.select('frindname','friendlink','firendimg','error')
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
                print(item[0],'友链重复了')

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
                print(item['title'],'文章重复了')
        query_list = query_leancloud()
        outdate(query_list, Friendspoor, time_limit)

    # 请求连接
    def get_data(link):
        r = requests.get(link, timeout=10)
        r.encoding = 'utf-8-sig'
        result = r.text
        return result

    # 通过sitemap请求
    def sitmap_get(user_info):
        print('\n')
        print('-------执行sitemap规则----------')
        print('执行链接：',user_info[1])
        link = user_info[1]
        error_sitmap = 'false'
        try:
            result = get_data(link + '/sitemap.xml')
        except:
            error_sitmap = 'true'
        soup = BeautifulSoup(result, 'html.parser')
        loc = soup.find_all('loc')
        post_link = loc[0].text
        result = get_data(post_link)
        soup = BeautifulSoup(result, 'html.parser')
        time = soup.find('time')
        title = soup.find('title')
        strtitle = title.text
        titlesplit = strtitle.split("|", 1)
        strtitle = titlesplit[0].strip()
        print(time.text)
        print(strtitle)
        print(post_link)
        print('-----------结束sitemap规则----------')
        print('\n')
        post_info = {
            'title': strtitle,
            'time': time.text,
            'link': post_link,
            'name': user_info[0],
            'img': user_info[2]
        }
        post_poor.append(post_info)
        return error_sitmap

    # 从主页获取文章
    def get_last_post(user_info):
        error_sitmap = 'false'
        link = user_info[1]
        result = get_data(link)
        soup = BeautifulSoup(result, 'html.parser')
        main_content = soup.find_all(id='recent-posts')
        time_excit = soup.find_all('time')
        if main_content and time_excit:
            error_sitmap = 'true'
            print('\n')
            print('-------执行主页规则----------')
            print('执行链接：',link)
            link_list = main_content[0].find_all('time',{"class": "post-meta-date-created"})
            if link_list == []:
                link_list = main_content[0].find_all('time')
            lasttime = datetime.datetime.strptime('1970-01-01', "%Y-%m-%d")
            for index, item in enumerate(link_list):
                link_date = item.get('datetime')
                time = link_date[0:10]
                if lasttime < datetime.datetime.strptime(time, "%Y-%m-%d"):
                    lasttime = datetime.datetime.strptime(time, "%Y-%m-%d")
            lasttime = lasttime.strftime('%Y-%m-%d')
            print('最新时间是',lasttime)
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
                    print(a.text)
                    print(link + a['href'])
                    print("-----------结束主页规则----------")
                    print('\n')
                    post_info = {
                        'title': a.text,
                        'time': lasttime,
                        'link': link + a['href'],
                        'name': user_info[0],
                        'img': user_info[2]
                    }
                    post_poor.append(post_info)
        else:
            error_sitmap = 'true'
        return error_sitmap

    # 主方法获取友链池
    
    # 引入leancloud验证
    leancloud.init(sys.argv[1], sys.argv[2])
    friendpage_link = sys.argv[3]

    # 执行主方法
    today = datetime.datetime.today()
    time_limit = 60
    result = get_data(friendpage_link)
    soup = BeautifulSoup(result, 'html.parser')
    main_content = soup.find_all(id='article-container')
    link_list = main_content[0].find_all('a')
    imglist = main_content[0].find_all('img')
    friend_poor = []
    post_poor = []
    for index, item in enumerate(link_list):
        link = item.get('href')
        name = item.get('title')
        try:
            img = imglist[index].get('data-lazy-src')
            print(img)
        except:
            img = ''
        if "#" in link:
            pass
        else:
            print(link)
            user_info = []
            user_info.append(name)
            user_info.append(link)
            user_info.append(img)
            friend_poor.append(user_info)

    total_count=0
    error_count=0
    for index, item in enumerate(friend_poor):
        error = 'false'
        try:
            total_count+=1
            error = get_last_post(item)
            if error == 'true':
                error = sitmap_get(item)
        except:
            print(item, "发生异常")
            error_count+=1
        item.append(error)
    print("一共进行%s次"% total_count)
    print("一共失败%s次"% error_count)
    leancloud_push_userinfo(friend_poor)
    post_poor.sort(key=itemgetter('time'), reverse=True)
    leancloud_push(post_poor)

main()
