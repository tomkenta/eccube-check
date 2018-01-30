import sys, json, os, argparse
import pandas as pd
from urllib.parse import urlparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from time import time
from logging import getLogger, FileHandler, StreamHandler, Formatter, DEBUG, WARN

# logging
logger = getLogger(__name__)
logger.setLevel(DEBUG)
# コンソール表示用
stream_handler = StreamHandler()
# ログファイル用
file_handler = FileHandler(filename='log/test.log')

formatter = Formatter(
    fmt="%(asctime)s [%(name)s Line:%(lineno)d] %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)

file_handler.setFormatter(formatter)
file_handler.setLevel(DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

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

    # 引数型チェック
    if isinstance(url, str):
        process.crawl('sources', start_urls=[url], allowed_domains=[domain])

    elif isinstance(url, list):
        process.crawl('sources', start_urls=url, allowed_domains=domain)
    else:
        logger.warning("eccube_check(url, domain): url/domain should be str or list")
        exit(1)

    # クロール開始
    process.start()


def crop_domain_from_url(url):
    '''urlからdomainを取る'''
    parsed_url = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_url)
    return domain


if __name__ == '__main__':
    logger.info("========================================%s========================================",
                "EC-CUBE クローリング開始")
    args_str = ' '.join(sys.argv)
    logger.info("実行したコマンド:%s" % args_str)

    start = time()
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

        url_data = csv_data['url']
        urls = url_data.tolist()
        domains = []

        for url in urls:
            domains.append(crop_domain_from_url(url))

        # urlによるcheck開始
        eccube_check(urls, domains)

        eccube_url_data = []
        with open('data/data.json', 'r') as f:
            if os.fstat(f.fileno()).st_size > 0:
                eccube_url_data = json.load(f)

        # 重複の解消 TODO:高速化の余地
        eccube_url_data_uniq = []
        for x in eccube_url_data:
            if x not in eccube_url_data_uniq:
                eccube_url_data_uniq.append(x)

        # SeriesからDataFrameに
        target_data = url_data.to_frame('url')
        # ec_cube列を初期化
        target_data['ec_cube'] = ""
        print(target_data)

        # ec_cubeを使っているurlsのリストを抽出
        eccube_urls = [ele["url"] for ele in eccube_url_data_uniq]

        for index in target_data.index:
            target_url = target_data.at[index, 'url']
            # https と 末尾の/対応
            # index のお陰で scrapyでitemをyieldする順番(eccube_urlsの順番)がわからなくても元データとの順番が保たれる
            if target_url in eccube_urls \
                    or target_url.replace('http', 'https') in eccube_urls \
                    or target_url + "/" in eccube_urls \
                    or target_url.replace('http', 'https') + "/" in eccube_urls:
                target_data.at[index, 'ec_cube'] = "EC-CUBE"
        print(target_data)
        # RDBの勉強必要
        output_data = pd.merge(csv_data, target_data, left_index=True, right_index=True, on='url')
        print(output_data)

        logger.debug("CSVに結果を出力")
        output_data.to_csv("data/output.csv")

        elapsed_time = time() - start
        logger.info("elapsed_time:{0}".format(elapsed_time) + "[sec]")
        logger.info("exit with 0")
        logger.info("========================================%s========================================",
                    "EC-CUBE クローリング終了")
        exit(0)

    else:
        parser.print_help()
        exit(0)
