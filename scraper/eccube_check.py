import sys, json, os, argparse
import pandas as pd
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

    # settings.pyから設定を得る
    settings = get_project_settings()
    # settings.update({
    #     "FEED_FORMAT": 'csv',
    #     "FEED_URI": 'data/data.csv'
    # })
    process = CrawlerProcess(settings)

    #引数型チェック
    if isinstance(url, str):
        process.crawl('sources', start_urls=[url], allowed_domains=[domain])

    elif isinstance(url, list):
        process.crawl('sources', start_urls=url, allowed_domains=domain)
    else:
        print("eccube_check(url, domain): url/domain should be str or list")
        exit(1)

    #クロール開始
    process.start()


def crop_domain_from_url(url):
    '''urlからdomainを取る'''
    parsed_url = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_url)
    return domain


if __name__ == '__main__':
    args = parser.parse_args()
    url = args.url
    csv = args.csv

    if url is not None:
        # data.jsonを空に
        with open('data/data.json', 'w') as f:
            f.write("")

        domain = crop_domain_from_url(url)

        # urlによるcheck開始
        eccube_check(url, domain)

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

    elif csv is not None:

        # data.jsonを空に
        with open('data/data.json', 'w') as f:
            f.write("")

        csv_data = pd.read_csv(csv)
        data = csv_data['url']
        urls = data.tolist()
        domains = []

        for url in urls:
            domains.append(crop_domain_from_url(url))

        # urlによるcheck開始
        eccube_check(urls, domains)

        print(csv_data)

        # ec-cube列を初期化
        csv_data['ec-cube'] = ''
        print(csv_data)



        #
        # with open('data/data.json', 'r') as f:
        #     if os.fstat(f.fileno()).st_size > 0:
        #         data = json.load(f)
        #     for ele in data:
        #         pattern = r"eccube"
        #         if ele:
        #             is_eccube = ele['ec_cube']
        #             if bool(is_eccube):
        #                 pass


    else:
        parser.print_help()
        exit(0)
