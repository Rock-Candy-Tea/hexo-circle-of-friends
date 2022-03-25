import scrapy

class XiaosoSpider(scrapy.Spider):
    name = 'xiaoso'
    allowed_domains = ['www.xiaoso.net']
    start_urls = ['https://www.xiaoso.net/']

    def parse(self, response):
        print("------xiaoso---------") # 打印网站文本