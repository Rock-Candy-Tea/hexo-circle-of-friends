# -*- coding:utf-8 -*-
# Author：yyyz
import datetime
import scrapy
import queue
import feedparser
import re
from scrapy.http.request import Request
from hexo_circle_of_friends.utils.get_url import GetUrl
from hexo_circle_of_friends.utils.regulations import reg_volantis, reg_normal
from hexo_circle_of_friends.utils.process_time import format_time
from hexo_circle_of_friends.utils.baselogger import get_logger

# from hexo_circle_of_friends import items todo use items

# 日志记录配置
logger = get_logger(__name__)
# post_parsers = ["theme_butterfly_parse"]
# 文章页解析器
post_parsers = [
    "post_feed_parse", "theme_butterfly_parse", "theme_fluid_parse", "theme_matery_parse", "theme_sakura_parse",
    "theme_volantis_parse", "theme_nexmoe_parse", "theme_next_parse", "theme_stun_parse", "theme_stellar_parse",
]
# 默认feed后缀
feed_suffix = [
    "atom.xml", "feed/atom", "rss.xml", "rss2.xml", "feed", "index.xml"
]


class CRequest(Request):
    def __init__(self, url, callback=None, meta=None, dont_filter=True,
                 errback=None,
                 *args, **kwargs):
        super(CRequest, self).__init__(url, callback, meta=meta, dont_filter=dont_filter,
                                       errback=errback, *args, **kwargs)


class FriendpageLinkSpider(scrapy.Spider):
    name = 'hexo_circle_of_friends'
    allowed_domains = ['*']
    start_urls = []

    def __init__(self, name=None, **kwargs):
        # 友链队列
        self.friend_poor = queue.Queue()

        self.friend_list = queue.Queue()
        self.today = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d')
        self.friend_url_parser = GetUrl()

        super(FriendpageLinkSpider, self).__init__(name, **kwargs)

    def start_requests(self):
        # 从配置文件导入友链列表
        if self.settings.get("SETTINGS_FRIENDS_LINKS").get("enable"):
            for li in self.settings.get("SETTINGS_FRIENDS_LINKS").get("list"):
                self.friend_poor.put(li)
        # 向gitee发送请求获取友链
        if self.settings["GITEE_FRIENDS_LINKS"]["enable"]:
            for number in range(1, 100):
                domain = 'https://gitee.com'
                dic = self.settings["GITEE_FRIENDS_LINKS"]
                url = domain + "/" + dic["owner"] + "/" + dic["repo"] + '/issues?state=' + dic[
                    "state"] + '&page=' + str(number)
                yield Request(url, callback=self.friend_poor_parse, meta={"gitee": {"domain": domain}})
        # 向github发送请求获取友链
        if self.settings["GITHUB_FRIENDS_LINKS"]["enable"]:
            for number in range(1, 100):
                domain = 'https://github.com'
                dic = self.settings["GITHUB_FRIENDS_LINKS"]
                url = domain + "/" + dic["owner"] + "/" + dic["repo"] + "/issues?page=" + str(number) + '&q=is%3A' + dic[
                    "state"]
                if dic["label"]:
                    url = url + '+label%3A' + dic["label"]
                yield Request(url, callback=self.friend_poor_parse, meta={"github": {"domain": domain}})
        # 初始化起始请求链接
        friendpage_link, friendpage_theme = self.init_start_urls()
        self.start_urls.extend(friendpage_link)
        for i, url in enumerate(self.start_urls):
            logger.info(f"起始url: {url}")
            yield Request(url, callback=self.friend_poor_parse, meta={"theme": friendpage_theme[i]})

    def init_start_urls(self):
        friendpage_link = []
        friendpage_theme = []
        if self.settings["DEBUG"]:
            for link_dic in self.settings["FRIENDPAGE_LINK"]:
                friendpage_link.append(link_dic["link"])
                friendpage_theme.append(link_dic["theme"])
        for item in self.settings["LINK"]:
            friendpage_link.append(item["link"])
            friendpage_theme.append(item["theme"])
        return friendpage_link, friendpage_theme

    def friend_poor_parse(self, response):
        # 从友链页解析出所有的友链信息
        # print("friend_poor_parse---------->" + response.url)

        # gitee解析
        if "gitee" in response.meta.keys():
            main_content = response.css("#git-issues a.title::attr(href)").extract()
            if main_content:
                for item in main_content:
                    issueslink = response.meta["gitee"]["domain"] + item
                    yield CRequest(issueslink, self.friend_poor_parse, meta={"gitee-issues": None})
        if "gitee-issues" in response.meta.keys():
            try:
                content = ''.join(response.css("code *::text").extract())
                user_info = []
                if self.settings["GITHUB_FRIENDS_LINKS"]["type"] == "volantis":
                    reg_volantis(user_info, content)
                    self.friend_poor.put(user_info)
                else:
                    info_list = ['name', 'link', 'avatar']
                    reg_normal(info_list, user_info, content)
                    if user_info[1] != '你的链接':
                        self.friend_poor.put(user_info)
            except:
                logger.warning("gitee友链获取失败")

        # github解析
        if "github" in response.meta.keys():
            main_content = response.css("div[aria-label=Issues] a.Link--primary::attr(href)").extract()
            if main_content:
                for item in main_content:
                    issueslink = response.meta["github"]["domain"] + item
                    yield CRequest(issueslink, self.friend_poor_parse, meta={"github-issues": None})
        if "github-issues" in response.meta.keys():
            try:
                content = ''.join(response.css("pre *::text").extract())
                if content != '':
                    user_info = []
                    if self.settings["GITHUB_FRIENDS_LINKS"]["type"] == "volantis":
                        reg_volantis(user_info, content)
                        self.friend_poor.put(user_info)
                    else:
                        info_list = ['name', 'link', 'avatar']
                        reg_normal(info_list, user_info, content)
                        if user_info[1] != '你的链接':
                            self.friend_poor.put(user_info)
            except:
                logger.warning("github友链获取失败")

        # 根据指定的theme主题解析
        if "theme" in response.meta.keys():
            theme = response.meta.get("theme")
            async_link = self.friend_url_parser.get_theme_url(theme, response, self.friend_poor)
            if async_link:
                # Yun主题的async_link临时解决
                yield CRequest(async_link, self.friend_poor_parse, meta={"async_link": async_link})
        # Yun主题async_link临时解决
        if "async_link" in response.meta.keys():
            self.friend_url_parser.Yun_async_link_handler(response, self.friend_poor)

        # 从友链队列逐个取出友链信息，对其主页发送请求
        while not self.friend_poor.empty():
            friend = self.friend_poor.get()
            # 统一url，结尾加"/"
            friend[1] += "/" if not friend[1].endswith("/") else ""
            if self.settings["SETTINGS_FRIENDS_LINKS"]['enable'] and len(friend) == 4:
                # 针对配置项中开启了自定义suffix的友链url进行处理
                url = friend[1] + friend[3]
                yield CRequest(url, self.post_feed_parse, meta={"friend": friend}, errback=self.errback_handler)
                self.friend_list.put(friend[:3])
                continue
            # 将友链添加到friend_list队列
            self.friend_list.put(friend)
            # 开始请求文章页
            for r in self.start_post_requests(friend[1], post_parsers, feed_suffix, meta={"friend": friend}):
                yield r

        # friend = ['小冰博客', 'https://blog.zzbd.org/', 'https://zfe.space/images/headimage.png']
        # friend = ['小冰博客', 'https://copur.xyz/', 'https://zfe.space/images/headimage.png']
        # [[1,1,1],[2,3,2]]
        # yield CRequest(friend[1], callback=self.theme_next_parse, meta={"friend": friend})

        # 将获取到的朋友列表传递到管道
        while not self.friend_list.empty():
            friend = self.friend_list.get()
            userdata = {}
            userdata["name"] = friend[0]
            userdata["link"] = friend[1]
            userdata["img"] = friend[2]
            userdata["userdata"] = "userdata"
            yield userdata

    def start_post_requests(self, domain, parsers, suffixs, meta, errback=None):
        errback = self.errback_handler if not errback else ...
        # 使用解析器依次尝试请求
        if not re.match("^http.?://", domain):
            return
        for p in parsers:
            parser = getattr(self, p)
            if p == "post_feed_parse":
                # 对于feed解析，使用默认feed后缀依次尝试请求
                for suffix in suffixs:
                    yield CRequest(domain + suffix, parser, meta, errback=errback)
            yield CRequest(domain, parser, meta, errback=errback)

    def post_feed_parse(self, response):
        # print("post_feed_parse---------->" + response.url)
        friend = response.meta.get("friend")
        d = feedparser.parse(response.text)
        version = d.version
        entries = d.entries
        l = len(entries) if len(entries) < 5 else 5
        try:
            init_post_info = self.init_post_info(friend, version)
            for i in range(l):
                entry = entries[i]
                # 标题
                title = entry.title
                # 链接
                link = entry.link
                self.process_link(link, friend[1])
                # 创建时间
                try:
                    created = entry.published_parsed
                except:
                    try:
                        created = entry.created_parsed
                    except:
                        created = entry.updated_parsed
                entrycreated = "{:4d}-{:02d}-{:02d}".format(created[0], created[1], created[2])
                # 更新时间
                try:
                    updated = entry.updated_parsed
                except:
                    try:
                        updated = entry.created_parsed
                    except:
                        updated = entry.published_parsed
                entryupdated = "{:4d}-{:02d}-{:02d}".format(updated[0], updated[1], updated[2])

                yield self.generate_postinfo(
                    init_post_info,
                    title,
                    entrycreated,
                    entryupdated,
                    link
                )
        except:
            pass

    def theme_butterfly_parse(self, response):
        # print("theme_butterfly_parse---------->" + response.url)
        rule = "butterfly"
        friend = response.meta.get("friend")
        titles = response.css("#recent-posts .recent-post-info a:first-child::text").extract()
        partial_l = response.css("#recent-posts .recent-post-info a:first-child::attr(href)").extract()
        createds = response.css("#recent-posts .recent-post-info .post-meta-date time:first-of-type::text").extract()
        updateds = response.css("#recent-posts .recent-post-info .post-meta-date time:nth-of-type(2)::text").extract()
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_fluid_parse(self, response):
        # print("theme_fluid_parse---------->" + response.url)
        rule = "fluid"
        friend = response.meta.get("friend")
        titles = response.css("#board .index-header a::text").extract()
        partial_l = response.css("#board .index-header a::attr(href)").extract()
        createds = response.css("#board .post-meta time::text").extract()
        updateds = []
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_matery_parse(self, response):
        # print("theme_matery_parse---------->" + response.url)
        rule = "matery"
        friend = response.meta.get("friend")
        titles = response.css("#articles .card .card-title::text").extract()
        partial_l = response.css("#articles .card a:first-child::attr(href)").extract()
        createds = response.css("#articles .card span.publish-date").re("\d{4}-\d{2}-\d{2}")
        updateds = []
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_sakura_parse(self, response):
        # print("theme_sakura_parse---------->" + response.url)
        rule = "sakura"
        friend = response.meta.get("friend")
        titles = response.css("#main a.post-title h3::text").extract()
        if not titles:
            res = re.findall("<body.*</body>", response.text)
            if res:
                text = res[0]
                sel = scrapy.Selector(text=text)
                titles = sel.css("body #main a.post-title h3::text").extract()
                links = sel.css("#main a.post-title::attr(href)").extract()
                createds = sel.css("#main .post-date::text").re("\d{4}-\d{1,2}-\d{1,2}")
            else:
                return
        else:
            links = response.css("#main a.post-title::attr(href)").extract()
            createds = response.css("#main .post-date::text").re("\d{4}-\d{1,2}-\d{1,2}")
        updateds = []
        try:
            for post_info in self.process_theme_postinfo(friend, links, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_volantis_parse(self, response):
        # print("theme_volantis_parse---------->" + response.url)
        rule = "volantis"
        friend = response.meta.get("friend")
        titles = response.css(".post-list .article-title a::text").extract()
        partial_l = response.css(".post-list .article-title a::attr(href)").extract()
        createds = response.css(".post-list .meta-v3 time::text").extract()
        updateds = []
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_nexmoe_parse(self, response):
        # print("theme_nexmoe_parse---------->" + response.url)
        rule = "nexmoe"
        friend = response.meta.get("friend")
        titles = response.css("section.nexmoe-posts .nexmoe-post h1::text").extract()
        partial_l = response.css("section.nexmoe-posts .nexmoe-post>a::attr(href)").extract()
        createds = response.css("section.nexmoe-posts .nexmoe-post-meta a:first-child::text").extract()
        updateds = []
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_stun_parse(self, response):
        # print("theme_stun_parse---------->" + response.url)
        rule = "stun"
        friend = response.meta.get("friend")
        titles = response.css("article .post-title__link::text").extract()
        partial_l = response.css("article .post-title__link::attr(href)").extract()
        createds = response.css("article .post-meta .post-meta-item--createtime .post-meta-item__value::text").extract()
        updateds = response.css("article .post-meta .post-meta-item--updatetime .post-meta-item__value::text").extract()
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_stellar_parse(self, response):
        # print("theme_stellar_parse---------->" + response.url)
        rule = "stellar"
        friend = response.meta.get("friend")
        titles = response.css(".post-list .post-card:not(.photo) .post-title::text").extract()
        partial_l = response.css(".post-list .post-card:not(.photo)::attr(href)").extract()
        createds = response.css(".post-list .post-card:not(.photo) #post-meta time::attr(datetime)").extract()
        updateds = []
        try:
            for post_info in self.process_theme_postinfo(friend, partial_l, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def theme_next_parse(self, response):
        # print("theme_next_parse---------->" + response.url)
        rule = "next/Yun"
        friend = response.meta.get("friend")
        base_css = ["article h2", "article .post-title", "article .post-title-link"]
        links_l = []
        for css in base_css:
            links = response.css("%s a:first-child::attr(href)" % css).extract()
            links_l.append(len(links))
        ind = links_l.index(max(links_l))
        links = response.css("%s a:first-child::attr(href)" % base_css[ind]).extract()
        titles = response.css("%s a:first-child::text" % base_css[ind]).extract()
        createds = response.css("article time[itemprop*=dateCreated]::text").extract()
        updateds = response.css("article time[itemprop=dateModified]::text").extract()
        try:
            for post_info in self.process_theme_postinfo(friend, links, titles, createds, updateds, rule):
                yield post_info
        except:
            pass

    def process_theme_postinfo(self, friend, links, titles, createds, updateds, rule):
        """
        :param friend: 文章对应的友链的信息
        :param links: 解析出的文章url列表
        :param titles: 解析出的文章标题列表
        :param createds: 解析出的文章创建时间列表
        :param updateds: 解析出的文章更新时间列表
        :param rule: 来自于哪个解析器（解析规则）
        """
        # 文章url不超过5篇
        l = len(links) if len(links) < 5 else 5
        # 处理标题列表
        titles = self.process_title(titles, l)
        # 处理创建时间和更新时间列表
        createds, updateds = self.process_time(createds, updateds, l)
        # 初始化文章信息数据
        init_post_info = self.init_post_info(friend, rule)
        # 如果既没有创建时间也没有更新时间则丢弃
        if not createds and not updateds:
            raise
        # 拼接文章信息
        for i in range(l):
            link = self.process_link(links[i], friend[1])
            yield self.generate_postinfo(
                init_post_info,
                titles[i],
                createds[i],
                updateds[i],
                link
            )

    def init_post_info(self, friend, rule):
        post_info = {
            "author": friend[0],
            "avatar": friend[2],
            "rule": rule
        }
        return post_info

    def process_link(self, link, domain):
        # 将link处理为标准链接
        if not re.match("^http.?://", link):
            link = domain + link.lstrip("/")
        return link

    def process_title(self, titles, lenth):
        """
        将title去除换行和回车以及两边的空格，并处理为长度不超过lenth的数组并返回
        :param titles: 文章标题列表
        :param lenth: 列表最大长度限制（取决于文章url列表）
        """
        if not titles:
            return None
        for i in range(lenth):
            if i < len(titles):
                titles[i] = titles[i].replace("\r", "").replace("\n", "").strip()
            else:
                # 如果url存在，但title不存在，会将title设置为"无题"
                titles.append("无题")
        return titles[:lenth]

    def process_time(self, createds, updateds, lenth):
        """
        将创建时间和更新时间格式化，并处理为长度统一且不超过lenth的数组并返回
        :param createds: 创建时间列表
        :param updateds: 更新时间列表
        :param lenth: 列表最大长度限制（取决于文章url列表）
        """
        # if both list are empty，return as fast as possible.
        if not createds and not updateds:
            return None, None
        # todo 格式化前根据过期时间预筛选
        c_len = len(createds)
        u_len = len(updateds)
        co = min(c_len, u_len)
        # 格式化长度
        for i in range(lenth):
            if i < co:
                # 交集部分
                createds[i] = createds[i].replace("\r", "").replace("\n", "").strip()
                updateds[i] = updateds[i].replace("\r", "").replace("\n", "").strip()
            elif i < u_len:
                # createds长度小于updateds，用updateds填充
                updateds[i] = updateds[i].replace("\r", "").replace("\n", "").strip()
                createds.append(updateds[i])
            elif i < c_len:
                # updateds长度小于createds，用createds填充
                createds[i] = createds[i].replace("\r", "").replace("\n", "").strip()
                updateds.append(createds[i])
            else:
                # 长度超出createds和updateds且小于lenth，用当前时间填充
                createds.append(self.today)
                updateds.append(self.today)
        # 格式化时间
        format_time(createds)
        format_time(updateds)
        return createds[:lenth], updateds[:lenth]

    def generate_postinfo(self, init_post_info, title, created, updated, link):
        post_info = init_post_info
        post_info["title"] = title
        post_info["created"] = created
        post_info["updated"] = updated
        post_info["link"] = link
        return post_info

    def errback_handler(self, error):
        # 错误回调
        # todo error???
        # print("errback_handler---------->")
        # print(error)
        # request = error.request
        # meta = error.request.meta
        pass
