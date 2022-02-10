from scrapy import Request
import json


def get_theme_url(theme, response, queue):
    # 根据主题获取要爬取的的友链列表，保存到user_info中
    if theme == "butterfly":
        get_butterfly_url(response, queue)
    if theme == "fluid":
        get_fluid_url(response, queue)
    if theme == "matery":
        get_matery_url(response, queue)
    if theme == "nexmoe":
        get_nexmoe_url(response, queue)
    if theme == "stun":
        get_stun_url(response, queue)
    if theme == "sakura":
        get_sakura_url(response, queue)
    if theme == "volantis":
        get_volantis_url(response, queue)
    if theme == "Yun":
        async_link = get_Yun_url(response, queue)
        return async_link
    if theme == "stellar":
        get_stellar_url(response, queue)


def get_butterfly_url(response, queue):
    avatar = response.css('.flink-list .info img::attr(data-lazy-src)').extract()
    if not avatar:
        avatar = response.css('.flink-list a img::attr(data-lazy-src)').extract()
    if not avatar:
        avatar = response.css('.flink-list a .info img::attr(src)').extract()
    if not avatar:
        avatar = response.css('.flink-list a img::attr(src)').extract()
    if not avatar:
        avatar = response.css('.flink .site-card .info img::attr(data-lazy-src)').extract()

    link = response.css('.flink-list a::attr(href)').extract()
    if not link:
        link = response.css('.flink .site-card::attr(href)').extract()

    name = response.css('.flink-list .flink-sitename::text').extract()
    if not name:
        name = response.css('.flink-list a .flink-item-name::text').extract()
    if not name:
        name = response.css('.flink .site-card .info .title::text').extract()
    handle(avatar, link, name, queue)


def get_fluid_url(response, queue):
    avatar = response.css('.link-avatar img::attr(src)').extract()
    link = response.css('.row.links a::attr(href)').extract()
    name = response.css('.link-title::text').extract()
    handle(avatar, link, name, queue)


def get_matery_url(response, queue):
    avatar = response.css('#friends-link .friend-div img::attr(src)').extract()
    link = response.css('#friends-link .friend-button>a::attr(href)').extract()
    name = response.css('#friends-link .friend-name::text').extract()
    handle(avatar, link, name, queue)


def get_nexmoe_url(response, queue):
    avatar = response.css('.nexmoe-py ul img::attr(data-src)').extract()
    link = response.css('.nexmoe-py ul a::attr(href)').extract()
    name = response.css('.nexmoe-py ul a::attr(title)').extract()
    handle(avatar, link, name, queue)


def get_stun_url(response, queue):
    avatar = response.css('.friends-plugin__item img::attr(data-src)').extract()
    link = response.css('.friends-plugin__item::attr(href)').extract()
    name = response.css('.friends-plugin__item-info__name::attr(title)').extract()
    handle(avatar, link, name, queue)


def get_sakura_url(response, queue):
    avatar = response.css('.link-item img::attr(src)').extract()
    link = response.css('.link-item a::attr(href)').extract()
    name = response.css('.link-item .sitename::text').extract()
    if name:
        for i, n in enumerate(name):
            name[i] = name[i].strip("\n ")
    handle(avatar, link, name, queue)


def get_volantis_url(response, queue):
    avatar = response.css('a.simpleuser img::attr(src)').extract()
    if not avatar:
        avatar = response.css('a.site-card img::attr(src)').extract()
    if not avatar:
        avatar = response.css('a.friend-card img::attr(src)').extract()

    link = response.css('a.simpleuser::attr(href)').extract()
    if not link:
        link = response.css('a.site-card::attr(href)').extract()
    if not link:
        link = response.css('a.friend-card::attr(href)').extract()

    name = response.css('a.simpleuser span::text').extract()
    if not name:
        name = response.css('a.site-card span::text').extract()
    if not name:
        name = response.css('a.friend-card span::text').extract()
    if not name:
        name = response.css('a.friend-card p::text').extract()
    handle(avatar, link, name, queue)


def get_Yun_url(response, queue):
    async_link = response.css("#links script::text").re("https://.*links\.json")[0]
    if async_link:
        return async_link
    avatar = response.css('#links a img::attr(src)').extract()
    link = response.css('#links a::attr(href)').extract()
    name = response.css('#links a::attr(title)').extract()

    handle(avatar, link, name, queue)


def get_stellar_url(response, queue):
    avatar = response.css('.card-link img::attr(data-src)').extract()
    link = response.css('.card-link::attr(href)').extract()
    name = response.css('.card-link span::text').extract()
    handle(avatar, link, name, queue)


def handle(avatar, link, name, queue):
    user_info = []
    n = min(len(avatar), len(link), len(name))
    if n != 0:
        for i in range(n):
            if link[i] == "":
                # 初步筛选掉不符合规则的link
                continue
            user_info.append(name[i])
            user_info.append(link[i])
            user_info.append(avatar[i])
            queue.put(user_info)
            user_info = []


def Yun_async_link_handler(response, queue):
    user_info = []
    friends = json.loads(response.text)
    for friend in friends:
        name = friend["name"]
        link = friend["url"]
        avatar = friend["avatar"]
        user_info.append(name)
        user_info.append(link)
        user_info.append(avatar)
        queue.put(user_info)
        user_info = []
