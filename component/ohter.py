"""
其他组件
"""
import yaml


def load_config():
    f = open('_config.yml', 'r', encoding='utf-8')
    ystr = f.read()
    ymllist = yaml.load(ystr, Loader=yaml.FullLoader)
    return ymllist


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
    return friend_postpoor
