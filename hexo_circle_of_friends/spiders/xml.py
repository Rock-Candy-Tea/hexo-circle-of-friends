from scrapy.spiders import XMLFeedSpider


class XmlSpider(XMLFeedSpider):
    name = 'xml'
    allowed_domains = ['*']
    start_urls = ['https://www.vwmwv.cn/feed/']
    iterator = 'html' # you can change this; see the docs
    itertag = 'rss' # change it accordingly

    def parse_node(self, response, selector):
        item = {}
        print(selector.xpath("//*").extract())
        r = selector.xpath("//title/text()").extract()
        t = selector.xpath("//guid/text()").extract()
        s = selector.xpath("//pubdate/text()").extract()
        print(r)
        print(t)
        print(s)
        # print(item)
        #item['url'] = selector.select('url').get()
        #item['name'] = selector.select('name').get()
        #item['description'] = selector.select('description').get()
        # return item
