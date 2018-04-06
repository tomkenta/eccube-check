import sys, json, os, argparse
import pandas as pd
from urllib.parse import urlparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from time import time
from datetime import datetime
from logging import getLogger, FileHandler, StreamHandler, Formatter, DEBUG, WARN

# path
dir_path = os.path.dirname(os.path.abspath(__file__))

# logging
logger = getLogger(__name__)
logger.setLevel(DEBUG)
# コンソール表示用
stream_handler = StreamHandler()
# ログファイル用
file_handler = FileHandler(filename=datetime.now().strftime(dir_path + '/log/test_%Y_%m_%d.log'))

formatter = Formatter(
    fmt="[%(asctime)s] %(levelname)-8s %(message)s :[%(name)s Line:%(lineno)d]", datefmt="%Y-%m-%d %H:%M:%S")

stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)

file_handler.setFormatter(formatter)
file_handler.setLevel(DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# コマンドライン用のパーサ
parser = argparse.ArgumentParser(
    prog='cart_check.py',
    description='eccube checker ',
    epilog='(end)',
    add_help=True
)

parser.add_argument('-u', '--url',
                    help='check one url OUTPUT: (input url used EC-CUBE /DO NOT use EC-CUBE )')
parser.add_argument('-c', '--csv',
                    help='check urls in csv OUTPUT: csv.')

# 添字よう
CART = 0
ERROR = 1


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


def is_atk(str):
    atks = ("運用中",
            "加盟再審査依頼済",
            "加盟審査NG",
            "加盟審査OK・承認依頼済",
            "加盟審査依頼済",
            "加盟審査承認済",
            "加盟審査中",
            "加盟審査保留",
            "加盟審査保留対応中",
            "加盟店解約済",
            "加盟店解約中",
            "加盟店解約予約済",
            "加盟店強制解約中",
            "契約棄却",
            "契約見送り",
            "成約(申込書受領済)")

    if str in atks:
        return True
    else:
        return False


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
        with open(dir_path + '/data/data.json', 'w') as f:
            f.write("")

        domain = crop_domain_from_url(url)

        # urlによるcheck開始
        cart_check(url, domain)

        with open(dir_path + '/data/data.json', 'r') as f:
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
        with open(dir_path + '/data/data.json', 'w') as f:
            f.write("")

        csv_data = pd.read_csv(csv)

        # 値がない場合は弾く
        url_data = csv_data['URL__C'].dropna()
        urls = url_data.tolist()
        domains = []

        for url in urls:
            domains.append(crop_domain_from_url(url))

        # urlによるcheck開始
        cart_check(urls, domains)

        cart_url_data = []
        with open(dir_path + '/data/data.json', 'r') as f:
            if os.fstat(f.fileno()).st_size > 0:
                cart_url_data = json.load(f)

        # 重複の解消 TODO:高速化の余地
        cart_url_data_uniq = []
        for x in cart_url_data:
            if x not in cart_url_data_uniq:
                cart_url_data_uniq.append(x)

        # SeriesからDataFrameに
        target_data = url_data.to_frame('URL__C')
        # cart, error 列を追加・初期化
        target_data['cart'] = ""
        target_data['error'] = ""
        print(target_data)

        dict = {ele['url']: [ele['cart'], ele['error']] for ele in cart_url_data_uniq}
        cart_urls = list(dict.keys())

        for index in target_data.index:
            target_url = target_data.at[index, 'URL__C']
            # indexのお陰でscrapyでitemをyieldする順番(cart_urlsの順番)がわからなくても元データとの順番が保たれる
            # https・末尾の/対応のための4パターン
            check_url_pattern = (target_url,
                                 target_url + "/",
                                 target_url.replace('http', 'https'),
                                 target_url.replace('http', 'https') + "/")
            for url in check_url_pattern:
                if url in cart_urls:
                    target_data.at[index, 'cart'] = dict[url][CART]
                    target_data.at[index, 'error'] = dict[url][ERROR]

        print('======= signed ===========')
        print(target_data)
        # url を基準に join
        output_data = pd.merge(csv_data, target_data, left_index=True, right_index=True, on='URL__C')
        print(output_data)

        # 判定できたカート数, 404
        v_counts = output_data['cart'].value_counts()
        e_counts = output_data['error'].value_counts()

        # データ採用ロジック部分
        for index in output_data.index:
            cart_from_crawler = output_data.at[index, 'cart']
            # パターン 1, 2
            if cart_from_crawler:
                if is_atk(output_data.at[index, 'ACCOUNTNAME__R.ACCOUNTSTATUS__R.NAME']):
                    continue
                else:
                    output_data.at[index, 'SHOPPINGCART__C'] = cart_from_crawler
            else:
                cart_from_sf = output_data.at[index, 'SHOPPINGCART__C']
                # パターン3
                if cart_from_sf:
                    if is_atk(output_data.at[index, 'ACCOUNTNAME__R.ACCOUNTSTATUS__R.NAME']):
                        continue
                    elif output_data.at[index, 'error'] == '404':
                        output_data.at[index, 'URL__C'] = ""

        output_data.to_csv("data/output/pwd_output.csv")
        logger.debug("CSVに結果を出力")

        # SFインポートに必要なデータだけを抽出
        d = output_data.loc[:, ['ID', 'URL__C', 'SHOPPINGCART__C']]
        d.to_csv("data/output/output.csv", index=False)

        elapsed_time = time() - start
        logger.info("elapsed_time:{0}".format(elapsed_time) + "[sec]")
        logger.info("checked count\n {}".format(v_counts))
        logger.info("404 count\n {}".format(e_counts))
        logger.info("exit with 0")
        logger.info("========================================%s========================================",
                    "EC-CUBE クローリング終了")
        exit(0)

    else:
        parser.print_help()
        exit(0)
