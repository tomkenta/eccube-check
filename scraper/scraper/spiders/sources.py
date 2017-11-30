# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import Source


class SourcesSpider(CrawlSpider):
    url = 'http://www.kawasaki-chintai.com/'
    name = 'sources'
    allowed_domains = [url]
    start_urls = [url]

    rules = (
        Rule(LinkExtractor(allow=r'.*'),
             callback='parse_start_url',
             follow=True,
             ),
    )

    def parse_start_url(self, response):
        """"start_urlsのインデックスページもスクレイピングする"""
        return self.parse_item(response)

    def parse_item(self, response):
        """"クロールしたページからItemをスクレイピングする"""
        # 1ページにつき1アイテムのみ
        for cut_html in response.xpath('//script/@src'):
            item = Source()
            item['src'] = cut_html.extract()

            yield item
