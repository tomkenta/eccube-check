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
import re

# logging
logger = getLogger(__name__)
logger.setLevel(DEBUG)
# コンソール表示用
stream_handler = StreamHandler()

formatter = Formatter(
    fmt="%(asctime)s [%(name)s Line:%(lineno)d] %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)

logger.addHandler(stream_handler)


class SourcesSpider(CrawlSpider):
    name = 'sources'
    # self.loggerに対するsetting
    custom_settings = {
        'LOG_FILE': 'log/test.log',
        'LOG_ENABLED': False,
        'LOG_FORMAT': '%(asctime)s [%(name)s Line:%(lineno)d] %(levelname)s - %(message)s',
        'LOG_DATEFORMAT': '%Y-%m-%d %H:%M:%S',
        'LOG_STDOUT': True
    }

    # メンテナンスされていないけどec-cubeを使っているページ用
    handle_httpstatus_list = [500]

    def start_requests(self):
        for url in self.start_urls:
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
                    res = {'cart': 'MODD', 'url': get_base_url(response)}
                    logger.info("MODD found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with MODD found")
                        raise CloseSpider("MODD found")

        if srcs:
            for i, src in enumerate(srcs):
                src_url = response.urljoin(src)
                logger.info("check url is {url}".format(url=src))

                if re.search(r"jquery", src):
                    continue

                # EC-CUBEのチェック
                elif re.search(r"eccube", src):
                    # 一回の場合は url は baseurlをget_base_urlを使って取る
                    res = {'cart': 'EC-CUBE', 'url': get_base_url(response)}
                    logger.info("EC-CUBE found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res
                    # 単一urlへのcheckの場合は止める
                    if len(self.start_urls) == 1:
                        logger.info("close spider with EC-CUBE found")
                        raise CloseSpider("EC-CUBE found")

                # Welcartのチェック
                elif re.search(r"usces_cart", src):
                    res = {'cart': 'Welcart', 'url': get_base_url(response)}
                    logger.info("Welcart found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with Welcart found")
                        raise CloseSpider("WelCart found")

                # Magentoのチェック
                elif re.search(r"/mage/", src) or re.search(r"/varien/", src):
                    res = {'cart': 'Magento', 'url': get_base_url(response)}
                    logger.info("Magento found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with Magento found")
                        raise CloseSpider("Magento found")

                # CS-Cartのチェック
                elif re.search(r"tygh", src):
                    res = {'cart': 'CS-Cart', 'url': get_base_url(response)}
                    logger.info("CS-Cart found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with CS-Cart found")
                        raise CloseSpider("CS-Cart found")

                # cartstarのチェック
                elif re.search(r"b4ff048c/application.js", src):
                    res = {'cart': 'cartstar', 'url': get_base_url(response)}
                    logger.info("cartstar found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res

                    if len(self.start_urls) == 1:
                        logger.info("close spider with cartstar found")
                        raise CloseSpider("cartstar found")

                else:
                    yield Request(src_url, callback=self.parse_code, errback=self.err_handle)
        else:
            logger.warning("index.html内にscript/@srcが見つかりませんせした: %s" % response.request.url)

    def parse_code(self, response):
        item = Source()
        downloaded_text = response.text[0:500]
        if "EC-CUBE" in downloaded_text:
            # 再帰的に取る場合は url は baseurlをrefererを使って取る
            item['cart'] = 'EC-CUBE'
            item['url'] = referer_str(response.request)
            logger.info("EC-CUBE found for %s", referer_str(response.request))
            yield item
            # 単一urlへのcheckの場合は止める
            if len(self.start_urls) == 1:
                logger.info("close spider with EC-CUBE found")
                raise CloseSpider("EC-CUBE found")

        # Magentoのチェック
        elif "Mage" in downloaded_text:
            item['cart'] = 'Magento'
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
            logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            logger.error('TimeoutError on %s', request.url)
        else:
            request = failure.request
            logger.error('UnhandledError on %s', request.url)
