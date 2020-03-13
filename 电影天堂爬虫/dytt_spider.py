#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: Thomas. Luo 
# time: 2020/3/12
import requests
from lxml import  etree
import pandas as pd
import re


headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
#1.获取第一页中详情页
def get_detail_url(url):
    response = requests.get(url, headers=headers)
    detail_html = etree.HTML(response.text)
    detail_urls = detail_html.xpath('//td/b/a/@href')
    return detail_urls

#2.获取影片详情
def parse_url(url):
    try:
        movie={}
        response = requests.get(url)
        text = response.content.decode('GBK')
        html = etree.HTML(text)
        title = html.xpath("//div[@class='title_all']/h1/font/text()")[0]
        movie['title'] = title
        zoomE = html.xpath("//div[@id='Zoom']")[0]
        cover = zoomE.xpath('.//img/@src')
        movie['cover'] = cover

        def pare_info(info, rule):
            return info.replace(rule, "").strip()

        infos = zoomE.xpath('.//text()')
        # print(infos)
        for index, info in enumerate(infos):
            if info.startswith("◎年　　代　"):
                year = pare_info(info, "◎年　　代　")
                movie['year'] = year
            elif info.startswith("◎产　　地　"):
                district = pare_info(info, "◎产　　地　")
                movie['district'] = district
            elif info.startswith("◎类　　别　"):
                type = pare_info(info, "◎类　　别　")
                movie['category'] = type
            elif info.startswith("◎语　　言　"):
                language = pare_info(info, "◎语　　言　")
                movie['language'] = language
            elif info.startswith("◎豆瓣评分　"):
                score = pare_info(info, "◎豆瓣评分　")
                movie['score'] = score
            elif info.startswith("◎片　　长　"):
                duration = pare_info(info, "◎片　　长　")
                movie['duration'] = duration
            elif info.startswith("◎导　　演　"):
                director = pare_info(info, "◎导　　演　")
                movie['director'] = director
            elif info.startswith("◎主　　演　"):
                info  = pare_info(info, "◎主　　演　")
                actors = [info]
                for x in range(index+1, len(infos)):
                    actor = infos[x].strip()
                    if actor.startswith("◎"):
                        break
                    actors.append(actor)
                movie['actors'] = actors
            elif info.startswith("◎简　　介"):
                profiles = infos[index+1].strip()
                movie['profiles'] = profiles
        # download = html.xpath('.//td[@bgcolor="#fdfddf"]/a/@href')[0]
        # movie['download'] = download
        return movie
    except UnicodeDecodeError:
        return "此网页解析失败"


def spider_main():
    base_url = "https://www.dytt8.net/html/gndy/dyzz/list_23_{}.html"
    movies = []
    for i in range(1, 8):
        #获取每页url
        first_url = base_url.format(i)
        #调用get_detail_url函数，获取详情页
        detail_url = get_detail_url(first_url)
        for url in detail_url:
            movie = parse_url("https://www.dytt8.net"+url)
            movies.append(movie)
            print(movie)

if __name__ == '__main__':
    spider_main()


