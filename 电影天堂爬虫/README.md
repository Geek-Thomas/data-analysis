# 电影天堂爬虫练习

- 这是一个小尝试，主要是使用requests库获取网页，并使用lxml中的xpath解析页面
- 练习任务是获取电影天堂中的2020最新影片的网页内容，并保存相关影片的详情信息
- 需要用到的爬虫库：requests, lxml

## 爬虫大致思路

- 首先打开**[电影天堂2020最新影片]( https://www.dy2018.com/html/gndy/dyzz/index.html )**首页，查看第二页，可通过更改index参数实现翻页功能

- 点击网页第一个元素**[ 2019年道恩强森奇幻冒险片《勇敢者游戏2：再战巅峰》BD中英双字](https://www.dy2018.com/i/101718.html)**，查看元素、使用xpath获取片名，评分以及影片信息

  

## 发送请求，获取详情页url

传入请求头

```python
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
```

解析网页，构造函数get_detail_url，传入参数url，得到页面中所有电影的url: detail_urls

```python
response = requests.get(url, headers=headers)
detail_html = etree.HTML(response.text)
detail_urls = detail_html.xpath('//td/b/a/@href')
#注意获得的detail_urls还需要经过拼接，才能调用
return detail_urls
```



## 解析详情页，获取info

解析网页，获得片名及封面图片

```python
response = requests.get(url)
text = response.content.decode('GBK')
html = etree.HTML(text)
title = html.xpath("//div[@class='title_all']/h1/font/text()")[0]
movies['title'] = title
zoomE = html.xpath("//div[@id='Zoom']")[0]
cover = zoomE.xpath('.//img/@src')
movies['cover'] = cover
infos = zoomE.xpath('.//text()')
```

进一步解析，获取影片详情info

这里在上面的函数中又定义了一个函数parse_info，用于处理info中的特殊字段

```python
def pare_info(info, rule):
    return info.replace(rule, "").strip()
```

遍历infos，得到年份，产地，类别，语言，豆瓣评分，片长，导演信息

```python
for index, info in enumerate(infos):
    if info.startswith("◎年　　代　"):
        year = pare_info(info, "◎年　　代　")
        movies['year'] = year
    elif info.startswith("◎产　　地　"):
        district = pare_info(info, "◎产　　地　")
        movies['district'] = district
```



![actor.jpg](C:\Users\28499\Desktop\actor.jpg)

由于演员有多个字段，需要进一步循环取出

```python
elif info.startswith("◎主　　演　"):
	info  = pare_info(info, "◎主　　演　")
	actors = [info]
	for x in range(index+1, len(infos)):
		actor = infos[x].strip()
		if actor.startswith("◎"):
			break
		actors.append(actor)
		movies['actors'] = actors
```

获取简介内容时，简介名与内容在两个标签中

![profile.jpg](C:\Users\28499\Desktop\profile.jpg)

```python
elif info.startswith("◎简　　介"):
	profiles = infos[index+1].strip()
	movies['profiles'] = profiles
```



## 构造主函数，调用上述函数

这里需要用到两个循环，第一个循环用于控制循环次数，第二个循环用于提取网页内容

```python
base_url = "https://www.dytt8.net/html/gndy/dyzz/list_23_{}.html"
movies = []
for i in range(1, 8):
    #获取每页url
    first_url = base_url.format(i)
    #调用get_detail_url函数，获取详情页
    detail_url = get_detail_url(first_url)
        for url in detail_url:
        movie_infos = parse_url("https://www.dytt8.net"+url)
        movies.append(movie_infos)
```



## 完整代码

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: Thomas. Luo 
# time: 2020/3/12
import requests
from lxml import  etree
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
        download = html.xpath('.//td[@bgcolor="#fdfddf"]/a/@href')[0]
        movie['download'] = download
        return movie
    except UnicodeDecodeError:
        return "此网页解析失败"

#3.调用函数
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
    print(movies)


if __name__ == '__main__':
    spider_main()

```

