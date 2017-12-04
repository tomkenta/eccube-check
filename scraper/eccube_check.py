import sys, json, re
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def eccube_check(url):
    """クロールの実行"""
    process = CrawlerProcess(get_project_settings())
    process.crawl('sources', start_urls=[url], allowed_domains=[url])
    process.start()


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 2:
        url = args[1]
        eccube_check(url)
    else:
        print("Usage : python eccube_check.py <url>")
        exit(0)

    f = open('data/data.json', 'r')
    data = json.load(f)
    f.close()

    for ele in data:
        pattern = r"eccube"
        src = ele['src']
        if re.search(pattern, src):
            print('This site used EC-CUBE')
            exit(0)

    print('NO EC-CUBE')
