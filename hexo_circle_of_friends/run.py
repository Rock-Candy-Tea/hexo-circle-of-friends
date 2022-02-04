from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from settings import *
def main():
    setting = get_project_settings()
    # init settings
    initsettings(setting)
    process = CrawlerProcess(setting)
    didntWorkSpider = ['xiaoso',]
    for spider_name in process.spiders.list():
        if spider_name in didntWorkSpider :
            continue
        # print("Running spider %s" % (spider_name))
        process.crawl(spider_name)
    process.start()

def initsettings(setting):
    if DATABASE == 'leancloud':
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.leancloud_pipe.LeancloudPipeline"] = 300
    elif DATABASE == 'mysql' or DATABASE== "sqlite":
        setting["ITEM_PIPELINES"]["hexo_circle_of_friends.pipelines.sql_pipe.SQLPipeline"] = 300

if __name__ == '__main__':
    main()