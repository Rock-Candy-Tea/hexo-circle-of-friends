import re
import json


def reg_normal(info_list, user_info, source):
    # print('----')
    for item in info_list:
        result = re.findall('(?<=' + item + ': ).*', source)
        result = result[0].replace('\r', '')
        user_info.append(result)


def reg_volantis(user_info, source):
    # print('----')
    dict_source = json.loads(source)
    user_info.append(dict_source["title"])
    user_info.append(dict_source["url"])
    user_info.append(dict_source["avatar"])
