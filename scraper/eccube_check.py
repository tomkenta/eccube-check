import sys, json, csv, os, argparse
from urllib.parse import urlparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# コマンドライン用のパーサ
parser = argparse.ArgumentParser(
    prog='eccube_check.py',
    description='eccube checker ',
    epilog='(end)',
    add_help=True
)

parser.add_argument('-u', '--url',
                    help='check one url OUTPUT: (input url used EC-CUBE /DO NOT use EC-CUBE )')
parser.add_argument('-c', '--csv',
                    help='check urls in csv OUTPUT: csv.')


def eccube_check(url, domain):
    """クロールの実行"""
    process = CrawlerProcess(get_project_settings())
    process.crawl('sources', start_urls=[url], allowed_domains=[domain])
    process.start()


if __name__ == '__main__':
    args = parser.parse_args()
    url = args.url
    csv = args.csv

    if url is not None:
        # data.jsonを空に
        with open('data/data.json', 'w') as f:
            f.write("")

        # urlからdomainを取る
        parsed_url = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_url)
        print(url)
        print(domain)

        # urlによるcheck開始
        eccube_check(url, domain)

    elif csv is not None:
        pass
    else:
        parser.print_help()
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
