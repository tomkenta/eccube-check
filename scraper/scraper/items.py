# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Quote(scrapy.Item):
    # define the fields for your item here like:
    author = scrapy.Field()
    text = scrapy.Field()
    tags = scrapy.Field()


class Source(scrapy.Item):
    cart = scrapy.Field()
    url = scrapy.Field()
    error = scrapy.Field()
