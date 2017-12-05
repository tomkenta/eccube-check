import sys, json, os
from urllib.parse import urlparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def eccube_check(url, domain):
    """クロールの実行"""
    process = CrawlerProcess(get_project_settings())
    process.crawl('sources', start_urls=[url], allowed_domains=[domain])
    process.start()


if __name__ == '__main__':
    args = sys.argv
    url = ""

    if len(args) == 2:
        # data.jsonを空に
        f = open('data/data.json', 'w')
        f.write("")
        f.close()

        url = args[1]
        parsed_url = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_url)
        print(url)
        print(domain)
        eccube_check(url, domain)
    else:
        print("Usage : python eccube_check.py <url>")
        exit(0)

    with open('data/data.json', 'r') as f:
        if os.fstat(f.fileno()).st_size > 0:
            data = json.load(f)
            for ele in data:
                pattern = r"eccube"
                if ele:
                    is_eccube = ele['ec_cube']
                    if bool(is_eccube):
                        print(url + ' uses EC-CUBE')
                        exit(0)

    print(url + 'DO NOT use EC-CUBE')
