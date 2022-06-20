################################请修改以下内容################################
# 友链页地址
# 参数说明：
# link：必填，在这里填写你的友链页面地址
# theme：必填，友链页的获取策略。需要指定该页面的主题，可选参数如下（这些是目前支持的主题）：
#   - common1: 通用主题1，请参考：https://fcircle-doc.js.cool/#/developmentdoc?id=友链页适配
#   - common2: 通用主题2，请参考：https://fcircle-doc.js.cool/#/developmentdoc?id=友链页适配
#   - butterfly：butterfly主题
#   - fluid：fluid主题
#   - matery：matery主题
#   - nexmoe：nexmoe主题
#   - stun：stun主题
#   - sakura: sakura主题
#   - volantis：volantis主题
#   - Yun：Yun主题
#   - stellar：stellar主题
# 支持配置多个友链页面并指定不同主题策略，每个用{}分隔，它们会被同时爬取，数据保存在一起。***至少配置一个***
LINK = [
    {
        "link": "https://gahotx.cn/link/",  # 友链页地址1，修改为你的友链页地址
        "theme": "butterfly"
    }
]

# 配置项友链
# enable：# 是否启用配置项友链 True/False（针对还未适配主题或者有定制需求的用户）
# json_api：通过api获取配置项友链，返回格式必须为：{"friends":[[友链1],[友链2],[友链3],[友链4]....]}，友链内容同LINK字段格式
# list字段填写格式：["name", "link", "avatar","suffix"]，其中：
#       name：必填，友链的名字
#       link：必填，友链主页地址
#       avatar：必填，头像地址
#       suffix：选填，自定义订阅后缀，主要针对不规范的网站订阅后缀，见示例2
SETTINGS_FRIENDS_LINKS = {
    "enable": True,
    "json_api": "",
    "list": [
        ["Butterfly", "https://github.com/jerryc127/hexo-theme-butterfly/commits/dev.atom", "https://cdn.gahotx.cn/photo/github.jpg"],
        ["Twikoo", "https://github.com/imaegoo/twikoo/commits/main.atom", "https://cdn.gahotx.cn/photo/github.jpg"],
        ["标签插件", "https://github.com/Akilarlxh/hexo-butterfly-tag-plugins-plus/commits/master.atom", "https://cdn.gahotx.cn/photo/github.jpg"]
        # 示例1：
        # ["贰猹の小窝", "https://noionion.top/", "https://pub-noionion.oss-cn-hangzhou.aliyuncs.com/head.jpg"],
        # ["Akilarの糖果屋", "https://akilar.top/", "https://akilar.top/images/headimage.png"],
        # 示例2：使用suffix的配置如下
        # 程序目前自动获取 "atom.xml", "feed/atom", "rss.xml", "rss2.xml", "feed", "index.xml" 这些后缀
        # 如果目标地址的后缀不在其中，就可以在这里添加
        # 比如 https://elizen.me/hello.xml ，填写：
        # ["elizen", "https://elizen.me/", "https://akilar.top/images/headimage.png", "hello.xml"],
    ]
}

# get links from gitee
# 从gitee issue中获取友链
GITEE_FRIENDS_LINKS = {
    "enable": False,  # True 开启gitee issue兼容
    "type": "normal",  # volantis/stellar用户请在这里填写volantis
    "owner": "ccknbc",  # 填写你的gitee用户名
    "repo": "blogroll",  # 填写你的gitee仓库名
    "state": "open"  # 填写抓取的issue状态(open/closed)
}

# get links from github
# 从github issue中获取友链
GITHUB_FRIENDS_LINKS = {
    "enable": False,  # True 开启github issue兼容
    "type": "normal",  # volantis/stellar用户请在这里填写volantis
    "owner": "ccknbc",  # 填写你的github用户名
    "repo": "ccknbc-actions",  # 填写你的github仓库名
    "state": "open"  # 填写抓取的issue状态(open/closed)
}

# block site list
# 添加屏蔽站点，支持正则表达式
BLOCK_SITE = [
    "https://gahotx.cn/"
]

# 启用HTTP代理，此项设为True，并且需要添加一个环境变量，名称为PROXY，值为[IP]:[端口]，比如：192.168.1.106:8080
HTTP_PROXY = False

# 过期文章清除（天）
OUTDATE_CLEAN = 60

# 存储方式，可选项：leancloud，mysql，sqlite，mongodb；默认为leancloud
DATABASE = "sqlite"

# 部署方式，可选项：github，server，docker；默认为github
DEPLOY_TYPE = "github"

################################请修改以上内容################################


##############################除非您了解本项目，否则请勿修改以下内容################################

VERSION = "4.3.2"

# debug
# debug模式
DEBUG = False

# lc
# debug模式使用
LC_APPID = "MTXYmy79JiLLO9VafgeAn8A-MdYXbMMI"
LC_APPKEY = "08N7lfcelf7Lkpy7Wp9amsiA"

# proxy
# HTTP_PROXY_URL = "192.168.1.106:10809"
HTTP_PROXY_URL = ""

# debug blog link url
# debug模式使用

# FRIENDPAGE_LINK = [
#     "https://yun.yunyoujun.cn/demo/", Yun
#     "https://akilar.top/link/",  # butterfly
#     "https://www.zyoushuo.cn/friends/",  # volantis
# ]
FRIENDPAGE_LINK = [
    {
        "link": "https://hgm.vercel.app/link/",  # 友链页地址1，修改为你的友链页地址
        "theme": "volantis"
    },
]


BOT_NAME = 'hexo_circle_of_friends'
LOG_LEVEL = "ERROR"
SPIDER_MODULES = ['hexo_circle_of_friends.spiders']
NEWSPIDER_MODULE = 'hexo_circle_of_friends.spiders'
USER_AGENT_LIST = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
]
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 128
DOWNLOAD_TIMEOUT = 15
COOKIES_ENABLED = False
DOWNLOADER_MIDDLEWARES = {
    # 'hexo_circle_of_friends.middlewares.HexoCircleOfFriendsDownloaderMiddleware': 543,
    'hexo_circle_of_friends.middlewares.RandomUserAgentMiddleware': 400,
    'hexo_circle_of_friends.middlewares.BlockSiteMiddleware': 300,
    'hexo_circle_of_friends.middlewares.ProxyMiddleware': 299,

}

ITEM_PIPELINES = {
    'hexo_circle_of_friends.pipelines.pipelines.DuplicatesPipeline': 200,
}

RETRY_ENABLED = True
