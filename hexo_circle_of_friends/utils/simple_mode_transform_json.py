import json
import os
from api_dependencies.sql import sqlapi
from hexo_circle_of_friends.utils.project import get_base_path


def transform():
    """
    极简模式，在github workflow中运行
    用于将data.db转换为data.json
    其中，data.json的格式与访问api `/all` 的相应格式相同（实际上就是调用了 `/all` 的函数）
    :return:
    """
    base_path = get_base_path()
    list_ = ['title', 'created', 'updated', 'link', 'author', 'avatar']
    data = sqlapi.query_all(list_, rule="created")
    with open(os.path.join(base_path, 'data.json'), "w") as f:
        json.dump(data, f)
    print(f"读取并转换完毕")


if __name__ == '__main__':
    transform()
