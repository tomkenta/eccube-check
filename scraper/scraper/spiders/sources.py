# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import Source
from scrapy.exceptions import *
import re


class SourcesSpider(CrawlSpider):
    name = 'sources'
    allowed_domains = ["kawasaki-chintai.com"]
    start_urls = ["http://www.kawasaki-chintai.com"]

    def parse(self, response):
        srcs = response.xpath('//script/@src').extract()

        for i, src in enumerate(srcs):
            src_url = response.urljoin(src)

            if re.search(r"eccube", src):
                yield {'ec_cube': 'True', 'url': src_url}
                raise CloseSpider("EC-CUBE found")

            yield Request(src_url, callback=self.parse_code)

    def parse_code(self, response):
        print("parse_code here")
        item = Source()

        is_eccube = "EC-CUBE" in response.text[0:500]
        if is_eccube:
            item['ec_cube'] = str(is_eccube)
            item['url'] = response.url
            yield item
            raise CloseSpider("EC-CUBE found")
