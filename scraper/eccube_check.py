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


def cart_check(url, domain):
    """クロールの実行"""

    # settings.pyから設定を得る
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    # 引数型チェック
    if isinstance(url, str):
        process.crawl('sources', start_urls=[url], allowed_domains=[domain])

    elif isinstance(url, list):
        process.crawl('sources', start_urls=url, allowed_domains=domain)
    else:
        logger.warning("cart_check(url, domain): url/domain should be str or list")
        exit(1)

    # クロール開始
    process.start()


def crop_domain_from_url(url):
    '''urlからdomainを取る'''
    parsed_url = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_url)
    return domain


if __name__ == '__main__':
    start = time()
    args = parser.parse_args()
    url = args.url
    csv = args.csv

    args_str = ' '.join(sys.argv)
    logger.info("========================================%s========================================",
                "EC-CUBE クローリング開始")
    logger.info("実行したコマンド:%s" % args_str)

if url is not None:
    # data.jsonを空に
    with open('data/data.json', 'w') as f:
        f.write("")

    domain = crop_domain_from_url(url)

    # urlによるcheck開始
    cart_check(url, domain)

    with open('data/data.json', 'r') as f:
        if os.fstat(f.fileno()).st_size > 0:
            data = json.load(f)
            for ele in data:
                if ele is not None:
                    cart = ele['cart']
                    print("{url}は{cart}を使用しています。".format(url=url, cart=cart))
                    exit(0)

        print("{url}はどのカートも使用していません。".format(url=url))

elif csv is not None:

    # data.jsonを空に
    with open('data/data.json', 'w') as f:
        f.write("")

    csv_data = pd.read_csv(csv)

    # 値がない場合は弾く
    url_data = csv_data['url'].dropna()
    urls = url_data.tolist()
    domains = []

    for url in urls:
        domains.append(crop_domain_from_url(url))

    # urlによるcheck開始
    cart_check(urls, domains)

    cart_url_data = []
    with open('data/data.json', 'r') as f:
        if os.fstat(f.fileno()).st_size > 0:
            cart_url_data = json.load(f)

    # 重複の解消 TODO:高速化の余地
    cart_url_data_uniq = []
    for x in cart_url_data:
        if x not in cart_url_data_uniq:
            cart_url_data_uniq.append(x)

    # SeriesからDataFrameに
    target_data = url_data.to_frame('url')
    # cart列を追加・初期化
    target_data['cart'] = ""
    print(target_data)

    cart_dict = {ele['url']: ele['cart'] for ele in cart_url_data_uniq}
    cart_urls = list(cart_dict.keys())

    for index in target_data.index:
        target_url = target_data.at[index, 'url']
        # indexのお陰でscrapyでitemをyieldする順番(cart_urlsの順番)がわからなくても元データとの順番が保たれる
        # https・末尾の/対応のための4パターン
        check_url_pattern = (target_url,
                             target_url + "/",
                             target_url.replace('http', 'https'),
                             target_url.replace('http', 'https') + "/")
        for url in check_url_pattern:
            if url in cart_urls:
                target_data.at[index, 'cart'] = cart_dict[url]

    output_data = pd.merge(csv_data, target_data, left_index=True, right_index=True, on='url')

    vc = output_data['cart'].value_counts()

    logger.debug("CSVに結果を出力")
    output_data.to_csv("data/output.csv")

    elapsed_time = time() - start
    logger.info("elapsed_time:{0}".format(elapsed_time) + "[sec]")
    logger.info("appear count\n {}".format(vc))
    logger.info("exit with 0")
    logger.info("========================================%s========================================",
                "EC-CUBE クローリング終了")
    exit(0)

else:
    parser.print_help()
    exit(0)
