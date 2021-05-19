import leancloud
import datetime

today = datetime.datetime.today()
time_limit = 60

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
    def repeat(link):
        upload = 'true'
        for query_item in query_list:
            url = query_item.get('link')
            if link == url:
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
        upload = repeat(item['link'])
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