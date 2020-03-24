# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re
from urllib.parse import quote
import json
from ..items import Comment360Item


class CommentspiderSpider(CrawlSpider):
    name = 'commentSpider'
    allowed_domains = ['zhushou.360.cn']
    start_urls = ['http://zhushou.360.cn']

    rules = (
        Rule(LinkExtractor(allow=r'zhushou\.360\.cn/detail/index/soft_id/\d+'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        item = Comment360Item()
        software = response.xpath('//h2[@id="app-name"]/span/text()').extract_first()
        score = response.xpath('//div[@class="pf"]/span[1]/text()').extract_first()
        downloadCounts = re.findall('<span class="s-3">下载：(.*?)次</span>', response.text)[0]
        item['software'] = software
        item['score'] = score
        item['downloadCounts'] = downloadCounts
        # 此处要完成拼接url， 获取baike_name
        pattern = re.compile("<script>.*?return.*?'baike_name': '(.*?)'.*'?</script>", re.S)
        baike_name = re.findall(pattern, response.text)[0]
        # print(baike_name)
        url = 'https://comment.mobilem.360.cn/comment/getComments?&baike='+ quote(baike_name) + '&start={}&count=10'
        for i in range(10):
            full_url = url.format(i)
            if full_url:
                # print(full_url)
                yield scrapy.Request(url=full_url, callback=self.parse_detail, meta={'item': item}, dont_filter=True)

    def parse_detail(self, response):
        item = response.meta['item']
        json_data = json.loads(response.body.decode())
        data = json_data['data']
        commentCounts = data['total']
        item['commentCounts'] = commentCounts
        item['comments'] = []
        for message in data['messages']:
            comments = {}
            comments['pubTime'] = message['create_time']
            comments['userName'] = message['username']
            comments['content']= message['content']
            comments['commentType'] = message['type']
            item['comments'].append(comments)
            yield item

    # software = scrapy.Field()
    # 评论数也是动态加载的，不能在网页中获得
    # commentCounts = scrapy.Field()
    # score = scrapy.Field()
    # userName = scrapy.Field()
    # commentType = scrapy.Field()
    # comments = scrapy.Field()
    # pubTime = scrapy.Field()
