# -*- coding: utf-8 -*-
import requests
requests.packages.urllib3.disable_warnings()

def get_data(link):
    result = ''
    user_agent = 'Mozilla/5.0 (Macintosh;Intel Mac OS X 10_12_6) ' \
                 'AppleWebKit/537.36(KHTML, like Gecko) ' \
                 'Chrome/67.0.3396.99Safari/537.36'
    header = {'User_Agent': user_agent}
    try:
        r = requests.get(link, headers=header, timeout=15,verify=False)
        r.encoding = 'utf-8'
        result = r.text.encode("gbk", 'ignore').decode('gbk', 'ignore')
        if str(r) == '<Response [404]>':
            result = 'error'
    except Exception as e:
        print(e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)
    return result

get_data('https://nekodeng.gitee.io/')