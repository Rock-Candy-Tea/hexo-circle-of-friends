# 获取朋友列表的url、name、avatar
# 每个函数负责一个功能
def get_avatar_url(response):
    # ------------- butterfly begin --------------- #
    avatar = response.css('.flink-list .info img::attr(data-lazy-src)').extract()
    if not avatar:
        avatar = response.css('.flink-list a img::attr(data-lazy-src)').extract()
    if not avatar:
        avatar = response.css('.flink-list a .info img::attr(src)').extract()
    if not avatar:
        avatar = response.css('.flink-list a img::attr(src)').extract()
    if not avatar:
        avatar = response.css('.flink .site-card .info img::attr(data-lazy-src)').extract()
    # ------------- butterfly end --------------- #

    # ------------- fluid begin --------------- #
    if not avatar:
        avatar = response.css('.link-avatar img::attr(src)').extract()
    # ------------- fluid end --------------- #

    # ------------- matery begin --------------- #
    if not avatar:
        avatar = response.css('#friends-link .friend-div img::attr(src)').extract()

    # ------------- sakura begin --------------- #
    if not avatar:
        avatar = response.css('.link-item img::attr(src)').extract()
    # ------------- sakura end --------------- #


    # ------------- volantis begin --------------- #
    if not avatar:
        avatar = response.css('a.simpleuser img::attr(src)').extract()
    if not avatar:
        avatar = response.css('a.site-card img::attr(src)').extract()
    if not avatar:
        avatar = response.css('a.friend-card img::attr(src)').extract()
    # ------------- volantis end --------------- #

    # ------------- nexmoe begin --------------- #
    if not avatar:
        avatar = response.css('.nexmoe-py ul img::attr(data-src)').extract()
    # ------------- nexmoe end --------------- #

    # ------------- Yun begin --------------- #
    if not avatar:
        avatar = response.css('#links a img::attr(src)').extract()
    # ------------- Yun end --------------- #

    # ------------- stun begin --------------- #
    if not avatar:
        avatar = response.css('.friends-plugin__item img::attr(data-src)').extract()
    # ------------- stun end --------------- #

    # ------------- stellar begin --------------- #
    if not avatar:
        avatar = response.css('.card-link img::attr(data-src)').extract()
    # ------------- stellar end --------------- #
    # print(avatar)
    return avatar


def get_link_url(response):
    # ------------- butterfly begin --------------- #
    link = response.css('.flink-list a::attr(href)').extract()
    if not link:
        link = response.css('.flink .site-card::attr(href)').extract()
    # ------------- butterfly end --------------- #

    # ------------- fluid begin --------------- #
    if not link:
        link = response.css('.row.links a::attr(href)').extract()
    # ------------- fluid end --------------- #

    # ------------- matery begin --------------- #
    if not link:
        link = response.css('#friends-link .friend-button>a::attr(href)').extract()
    # ------------- matery end --------------- #

    # ------------- sakura begin --------------- #
    if not link:
        link = response.css('.link-item a::attr(href)').extract()
    # ------------- sakura end --------------- #

    # ------------- volantis begin --------------- #
    if not link:
        link = response.css('a.simpleuser::attr(href)').extract()
    if not link:
        link = response.css('a.site-card::attr(href)').extract()
    if not link:
        link = response.css('a.friend-card::attr(href)').extract()
    # ------------- volantis end --------------- #

    # ------------- nexmoe begin --------------- #
    if not link:
        link = response.css('.nexmoe-py ul a::attr(href)').extract()
    # ------------- nexmoe end --------------- #


    # ------------- Yun begin --------------- #
    if not link:
        link = response.css('#links a::attr(href)').extract()
    # ------------- Yun end --------------- #

    # ------------- stun begin --------------- #
    if not link:
        link = response.css('.friends-plugin__item::attr(href)').extract()
    # ------------- stun end --------------- #

    # ------------- stellar begin --------------- #
    if not link:
        link = response.css('.card-link::attr(href)').extract()
    # ------------- stellar end --------------- #
    # print(link)
    return link


def get_name_url(response):
    # ------------- butterfly begin --------------- #
    name = response.css('.flink-list .flink-sitename::text').extract()
    if not name:
        name = response.css('.flink-list a .flink-item-name::text').extract()
    if not name:
        name = response.css('.flink .site-card .info .title::text').extract()
    # ------------- butterfly end --------------- #

    # ------------- fluid begin --------------- #
    if not name:
        name = response.css('.link-title::text').extract()
    # ------------- fluid end --------------- #

    # ------------- matery begin --------------- #
    if not name:
        name = response.css('#friends-link .friend-name::text').extract()
    # ------------- matery end --------------- #

    # ------------- sakura begin --------------- #
    if not name:
        name = response.css('.link-item .sitename::text').extract()
        if name:
            for i ,n in enumerate(name):
                name[i ] =name[i].strip("\n ")
    # ------------- sakura end --------------- #

    # ------------- volantis begin --------------- #
    if not name:
        name = response.css('a.simpleuser span::text').extract()
    if not name:
        name = response.css('a.site-card span::text').extract()
    if not name:
        name = response.css('a.friend-card span::text').extract()
    if not name:
        name = response.css('a.friend-card p::text').extract()
    # ------------- volantis end --------------- #


    # ------------- nexmoe begin --------------- #
    if not name:
        name = response.css('.nexmoe-py ul a::attr(title)').extract()
    # ------------- nexmoe end --------------- #

    # ------------- Yun begin --------------- #
    if not name:
        name = response.css('#links a::attr(title)').extract()
    # ------------- Yun end --------------- #

    # ------------- stun begin --------------- #
    if not name:
        name = response.css('.friends-plugin__item-info__name::attr(title)').extract()
    # ------------- stun end --------------- #

    # ------------- stellar begin --------------- #
    if not name:
        name = response.css('.card-link span::text').extract()
    # ------------- stellar end --------------- #
    # print(name)
    return name