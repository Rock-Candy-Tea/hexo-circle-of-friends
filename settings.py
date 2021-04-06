"""
全局设置

所有变量名必须大写，否则不读取

使用方法：

在需要使用设置变量的py文件引入settings处理器即可

示例(/handlers/exsample.py)：
from handlers.coreSettings import config

# settings.py变量的使用
print(config.BASE_PATH)

# 载入的yml文件的使用,数据结构与原来一致
print(config.yml)

"""
import os


# 项目ROOT地址
BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# debug模式
DEBUG = True

# debug leancloud验证
LC_APPID = "nSyYINNelN3OJdAbblDVNWM1-MdYXbMMI"
LC_APPKEY = "yxmDsLg0reOEa0DXfW8cfnee"

# debug 测试用的博客地址
# FRIENPAGE_LINK = "https://nekodeng.gitee.io/friends/"
FRIENPAGE_LINK = "https://zhangyazhuang.gitee.io/link/"
# FRIENPAGE_LINK = "https://blog.raxianch.moe/link"


# 网页请求器
# TODO 未实装
# 超时(单位:秒)
TIMEOUT = 10
SSL = False
RETRY_MAX = 5


# 链接处理设置

# 屏蔽站点
BLOCK_SITE = [
    "https://example.com/",
]

# 其他设置
# TODAY = datetime.datetime.today()
# TIME_limit = 60