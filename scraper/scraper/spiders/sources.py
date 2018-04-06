# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.spiders import CrawlSpider
from ..items import Source
from scrapy.exceptions import *
from scrapy.utils.request import referer_str
from scrapy.utils.response import get_base_url
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from logging import getLogger, StreamHandler, Formatter, DEBUG
from datetime import datetime
from enum import Enum
import re, os

# logging
logger = getLogger(__name__)
logger.setLevel(DEBUG)
# コンソール表示用
stream_handler = StreamHandler()

formatter = Formatter(
    fmt="[%(asctime)s] %(levelname)-8s %(message)s :[%(name)s Line:%(lineno)d]", datefmt="%Y-%m-%d %H:%M:%S")
stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)

logger.addHandler(stream_handler)

# path
dir_path = os.path.dirname(os.path.abspath(__file__))


class Cart(str, Enum):
    ec_cube = "EC-CUBE"
    welcart = "Welcart"
    magento = "Magento"
    cs_cart = "CS-Cart"
    cartstar = "cartstar"
    modd = "MODD"
    makeshop = "MakeShop"
    shopify = "Shopify"


class SourcesSpider(CrawlSpider):
    name = 'sources'
    # self.loggerに対するsetting
    custom_settings = {
        'LOG_FILE': datetime.now().strftime(dir_path + '/log/test_%Y_%m_%d.log'),
        'LOG_ENABLED': False,
        'LOG_FORMAT': '[%(asctime)s] %(levelname)-8s %(message)s :[%(name)s Line:%(lineno)d]"',
        'LOG_DATEFORMAT': '%Y-%m-%d %H:%M:%S',
        'LOG_STDOUT': True
    }

    # メンテナンスされていないけどec-cubeを使っているページ用
    handle_httpstatus_list = [500]

    def start_requests(self):
        for url in self.start_urls:
            if "rakuten" not in url and "yahoo" not in url:
                try:
                    yield Request(url, callback=self.parse, errback=self.err_handle)

                except ValueError:
                    logger.error("不正なURLを検知 :%s" % url)
                    pass

                except:
                    logger.error("スタート時にエラーの発生 :%s" % url)
                    raise CloseSpider("異常終了")

    def parse(self, response):
        srcs = response.xpath('//script/@src').extract()
        hrefs = response.xpath('//a/@href').extract()

        if hrefs is not None:
            for i, href in enumerate(hrefs):
                # MODDのチェック
                if re.search(r"modd", href) or re.search(r"ShoppingCart.aspx", href):
                    res = {'cart': Cart.modd, 'url': get_base_url(response)}
                    logger.info("MODD found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with MODD found")
                        raise CloseSpider("MODD found")

        if srcs is not None:
            for i, src in enumerate(srcs):
                src_url = response.urljoin(src)

                if re.search(r"jquery", src):
                    # jquery下でのmakeshopのチェック
                    if re.search(r"makeshop", src):
                        res = {'cart': Cart.makeshop, 'url': get_base_url(response)}
                        logger.info("makeshop found for %s", get_base_url(response))
                        logger.debug(str(res))
                        yield res

                        if len(self.start_urls) == 1:
                            logger.info("close spider with makeshop found")
                            raise CloseSpider("makeshop found")

                    continue

                # EC-CUBEのチェック
                elif re.search(r"eccube", src):
                    # 一回の場合は url は baseurlをget_base_urlを使って取る
                    res = {'cart': Cart.ec_cube, 'url': get_base_url(response)}
                    logger.info("EC-CUBE found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res
                    # 単一urlへのcheckの場合は止める
                    if len(self.start_urls) == 1:
                        logger.info("close spider with EC-CUBE found")
                        raise CloseSpider("EC-CUBE found")

                # Welcartのチェック
                elif re.search(r"usces_cart", src):
                    res = {'cart': Cart.welcart, 'url': get_base_url(response)}
                    logger.info("Welcart found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with Welcart found")
                        raise CloseSpider("WelCart found")

                # Magentoのチェック
                elif re.search(r"/mage/", src) or re.search(r"/varien/", src):
                    res = {'cart': Cart.magento, 'url': get_base_url(response)}
                    logger.info("Magento found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with Magento found")
                        raise CloseSpider("Magento found")

                # CS-Cartのチェック
                elif re.search(r"tygh", src):
                    res = {'cart': Cart.cs_cart, 'url': get_base_url(response)}
                    logger.info("CS-Cart found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with CS-Cart found")
                        raise CloseSpider("CS-Cart found")

                # cartstarのチェック
                elif re.search(r"b4ff048c/application.js", src):
                    res = {'cart': Cart.cartstar, 'url': get_base_url(response)}
                    logger.info("cartstar found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with cartstar found")
                        raise CloseSpider("cartstar found")

                # makeshopのチェック
                elif re.search(r"makeshop", src):
                    res = {'cart': Cart.makeshop, 'url': get_base_url(response)}
                    logger.info("makeshop found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with makeshop found")
                        raise CloseSpider("makeshop found")

                # Shopifyのチェック
                elif re.search(r"cdn.shopify.com", src):
                    res = {'cart': Cart.shopify, 'url': get_base_url(response)}
                    logger.info("Shopify found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with Shopify found")
                        raise CloseSpider("Shopify found")

                else:
                    yield Request(src_url, callback=self.parse_code, errback=self.err_handle)
        else:
            logger.warning("index.html内にscript/@srcが見つかりませんせした: %s" % response.request.url)

    def parse_code(self, response):
        item = Source()
        downloaded_text = response.text[0:500]
        if "EC-CUBE" in downloaded_text:
            # 再帰的に取る場合は url は baseurlをrefererを使って取る
            item['cart'] = Cart.ec_cube
            item['url'] = referer_str(response.request)
            logger.info("EC-CUBE found for %s", referer_str(response.request))
            yield item
            # 単一urlへのcheckの場合は止める
            if len(self.start_urls) == 1:
                logger.info("close spider with EC-CUBE found")
                raise CloseSpider("EC-CUBE found")

        # Magentoのチェック
        elif "Mage" in downloaded_text:
            item['cart'] = Cart.magento
            item['url'] = referer_str(response.request)
            logger.info("Magento found for %s", referer_str(response.request))
            yield item
            # 単一urlへのcheckの場合は止める
            if len(self.start_urls) == 1:
                logger.info("close spider with Magento found")
                raise CloseSpider("Magento found")

    def err_handle(self, failure):
        logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            res = {'cart': '', 'url': request.url, 'error': "404"}
            logger.error('DNSLookupError on %s', request.url)
            logger.debug(str(res))
            yield res


        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            logger.error('TimeoutError on %s', request.url)
        else:
            request = failure.request
            logger.error('UnhandledError on %s', request.url)
