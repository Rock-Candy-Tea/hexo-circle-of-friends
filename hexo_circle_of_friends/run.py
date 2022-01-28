from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

def main():
    setting = get_project_settings()
    process = CrawlerProcess(setting)
    didntWorkSpider = ['xiaoso','hexo_circle_of_friends']
    for spider_name in process.spiders.list():
        if spider_name in didntWorkSpider :
            continue
        print("Running spider %s" % (spider_name))
        process.crawl(spider_name)
    process.start()

if __name__ == '__main__':
    main()