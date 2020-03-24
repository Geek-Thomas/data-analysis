# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Comment360Item(scrapy.Item):
    # 这里选择我们要爬取的内容：软件名，评论总数，评分，下载量，用户名，评论类型以及评论时间
    software = scrapy.Field()
    commentCounts = scrapy.Field()
    score = scrapy.Field()
    downloadCounts = scrapy.Field()
    userName = scrapy.Field()
    commentType = scrapy.Field()
    comments = scrapy.Field()
    pubTime = scrapy.Field()
    content = scrapy.Field()


