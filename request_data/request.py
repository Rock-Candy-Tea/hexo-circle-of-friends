#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2021/3/6
# CreatTIME : 16:02 
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

import requests
import chardet
import yaml
import os.path
from urllib.parse import unquote, urlparse
from handlers.coreSettings import configs as config
from request_data.middleware import RandomUserAgentMiddleware
from request_data.middleware import contentChardetMiddleware
requests.packages.urllib3.disable_warnings()


def get_data(link):
    """
    获取网页
    :param link: 请求的网页地址
    :return: str, result
    """
    # 载入配置文件
    # 甭载了，载过了

    # UA对象
    ua = RandomUserAgentMiddleware()
    # 链接解析
    urlInfo = urlparse(link)
    # 请求信息
    timeout = config.yml['setting']['request']['timeout']
    verify = config.yml['setting']['request']['ssl']
    headers = {
        'Accept-Encoding': 'deflate',
        "Referer": f"{urlInfo.scheme}://{urlInfo.netloc}",
        'User_Agent': ua.roll_ua()
    }
    # 回调
    result = "error"
    try:
        # 网页请求成功
        r = requests.get(url=link, headers=headers, timeout=timeout, verify=verify)

        # 获取网页编码格式，并修改为request.text的解码类型
        char = contentChardetMiddleware()
        r.encoding = char.encoding_2_encoding(chardet.detect(r.content)['encoding'])

        # 网页请求OK或者请求得到的内容过少，判断为连接失败
        if (not r.ok) or len(r.content) < 500 or r.status_code > 400:
            raise ConnectionError
        else:
            result = r.text
            return result

    except Exception:
        count = 0  # 重试次数
        while count < 5:
            try:
                r = requests.get(url=link, headers=headers, timeout=timeout, verify=verify)
                # 获取网页编码格式，并修改为request.text的解码类型
                char = contentChardetMiddleware()
                r.encoding = char.encoding_2_encoding(chardet.detect(r.content)['encoding'])
                if (not r.ok) or len(r.content) < 500 or r.status_code > 400:
                    raise ConnectionError
                else:
                    result = r.text
                    return result
            except Exception:
                count += 1
    finally:
        return result


if __name__ == '__main__':
    print(get_data("https://nekodeng.gitee.io"))