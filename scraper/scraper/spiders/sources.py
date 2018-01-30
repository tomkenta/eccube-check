# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import Source
from scrapy.exceptions import *
from scrapy.utils.request import referer_str
from scrapy.utils.response import get_base_url
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
import re
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

    # allowed_domains = ["kawasaki-chintai.com"]
    # start_urls = ["http://www.kawasaki-chintai.com"]

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

        if srcs:
            for i, src in enumerate(srcs):
                src_url = response.urljoin(src)

                if re.search(r"eccube", src):
                    # 一回の場合は url は baseurlをget_base_urlを使って取る
                    res = {'ec_cube': 'True', 'url': get_base_url(response)}
                    logger.info("EC-CUBE found for %s", get_base_url(response))
                    logger.debug(str(res))
                    yield res
                    # 単一urlへのcheckの場合は止める
                    if len(self.start_urls) == 1:
                        logger.info("close spider with EC-CUBE found")
                        raise CloseSpider("EC-CUBE found")

                elif re.search(r"jquery", src):
                    # logger.debug("jQueryのsrcはスキップします:%s", src)
                    continue
                else:
                    yield Request(src_url, callback=self.parse_code, errback=self.err_handle)
        else:
            logger.warning("index.html内にscript/@srcが見つかりませんせした: %s" % response.request.url)

    def parse_code(self, response):
        item = Source()

        is_eccube = "EC-CUBE" in response.text[0:500]
        if is_eccube:
            # 再帰的に取る場合は url は baseurlをrefererを使って取る
            item['ec_cube'] = str(is_eccube)
            item['url'] = referer_str(response.request)
            logger.info("EC-CUBE found for %s", referer_str(response.request))
            yield item
            # 単一urlへのcheckの場合は止める
            if len(self.start_urls) == 1:
                logger.info("close spider with EC-CUBE found")
                raise CloseSpider("EC-CUBE found")

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
