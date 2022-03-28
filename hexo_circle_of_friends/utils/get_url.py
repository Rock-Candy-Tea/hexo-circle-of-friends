import json


class GetUrl:

    def __init__(self):
        self.strategies = ["common1","common2", "butterfly", "fluid", "matery", "nexmoe", "stun", "sakura", "volantis", "Yun","stellar"]

    def get_theme_url(self,theme, response, queue):
        # 根据主题获取要爬取的的友链列表，保存到user_info中
        for strategy in self.strategies:
            if strategy == theme:
                parser = getattr(self,"get_"+theme+"_url")
                async_link = parser(response,queue)
                return async_link

    def get_common1_url(self,response,queue):
        avatar = response.css('.cf-friends img::attr(src)').extract()
        link = response.css('.cf-friends a::attr(href)').extract()
        name = response.css('.cf-friends a::text').extract()
        self.handle(avatar, link, name, queue)

    def get_common2_url(self,response,queue):
        avatar = response.css('.cf-friends-avatar::attr(data-lazy-src)').extract()
        if not avatar:
            avatar = response.css('img.cf-friends-avatar::attr(src)').extract()
        link = response.css('a.cf-friends-link::attr(href)').extract()
        name = response.css('.cf-friends-name::text').extract()
        self.handle(avatar, link, name, queue)

    def get_butterfly_url(self,response, queue):
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
        self.handle(avatar, link, name, queue)


    def get_fluid_url(self,response, queue):
        avatar = response.css('.card img::attr(src)').extract()
        link = response.css('.card a::attr(href)').extract()
        name = response.css('.card .link-title::text').extract()
        self.handle(avatar, link, name, queue)


    def get_matery_url(self,response, queue):
        avatar = response.css('#friends-link .frind-ship img::attr(src)').extract()
        link = response.css('#friends-link .frind-ship a::attr(href)').extract()
        name = response.css('#friends-link .frind-ship h1::text').extract()
        self.handle(avatar, link, name, queue)


    def get_nexmoe_url(self,response, queue):
        avatar = response.css('.nexmoe-py ul img::attr(data-src)').extract()
        link = response.css('.nexmoe-py ul a::attr(href)').extract()
        name = response.css('.nexmoe-py ul a::attr(title)').extract()
        self.handle(avatar, link, name, queue)


    def get_stun_url(self,response, queue):
        avatar = response.css('.friends-plugin__item img::attr(data-src)').extract()
        link = response.css('.friends-plugin__item::attr(href)').extract()
        name = response.css('.friends-plugin__item-info__name::attr(title)').extract()
        self.handle(avatar, link, name, queue)


    def get_sakura_url(self,response, queue):
        avatar = response.css('.link-item img::attr(src)').extract()
        link = response.css('.link-item a::attr(href)').extract()
        name = response.css('.link-item .sitename::text').extract()
        if name:
            for i, n in enumerate(name):
                name[i] = name[i].strip("\n ")
        self.handle(avatar, link, name, queue)


    def get_volantis_url(self,response, queue):
        avatar = response.css('a.simpleuser img::attr(src)').extract()
        if not avatar:
            avatar = response.css('a.site-card img::attr(src)').extract()
        if not avatar:
            avatar = response.css('a.friend-card img::attr(src)').extract()
        if not avatar:
            avatar = response.css('.content a.flat-box img::attr(src)').extract()

        link = response.css('a.simpleuser::attr(href)').extract()
        if not link:
            link = response.css('a.site-card::attr(href)').extract()
        if not link:
            link = response.css('a.friend-card::attr(href)').extract()
        if not link:
            link = response.css('.content a.flat-box::attr(href)').extract()

        name = response.css('a.simpleuser span::text').extract()
        if not name:
            name = response.css('a.site-card span::text').extract()
        if not name:
            name = response.css('a.friend-card span::text').extract()
        if not name:
            name = response.css('a.friend-card p::text').extract()
        if not name:
            name = response.css('.content a.flat-box::text').extract()
        self.handle(avatar, link, name, queue)


    def get_Yun_url(self,response, queue):
        async_link = response.css("#links script::text").re("https://.*links\.json")[0]
        if async_link:
            return async_link
        avatar = response.css('#links a img::attr(src)').extract()
        link = response.css('#links a::attr(href)').extract()
        name = response.css('#links a::attr(title)').extract()

        self.handle(avatar, link, name, queue)


    def get_stellar_url(self,response, queue):
        avatar = response.css('.card-link img::attr(data-src)').extract()
        link = response.css('.card-link::attr(href)').extract()
        name = response.css('.card-link span::text').extract()
        self.handle(avatar, link, name, queue)


    def handle(self,avatar, link, name, queue):
        user_info = []
        n = min(len(avatar), len(link), len(name))
        # print(name,link,avatar)
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


    def Yun_async_link_handler(self,response, queue):
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
