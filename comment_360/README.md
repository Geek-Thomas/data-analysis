# 使用scrapy爬取360手机助手app评论

爬取目标：爬取360手机商店中的各app下载量，评分，评论总数，各用户评论(bad,good,best) ，每个大概爬取100条。

网站分析：从[360手机助手](http://zhushou.360.cn/detail/index/soft_id/77208)网页开始，使用crawlspider批量爬取。在网页可以获得app名字，下载量，评分。需要注意的是，评论是ajax数据，通过解析网页，找到评论对应的[js]([https://comment.mobilem.360.cn/comment/getComments?callback=jQuery17209063329175179409_1585033247845&baike=360%E6%89%8B%E6%9C%BA%E5%8D%AB%E5%A3%AB&c=message&a=getmessage&start=0&count=10&_=1585033248931](https://comment.mobilem.360.cn/comment/getComments?callback=jQuery17209063329175179409_1585033247845&baike=360手机卫士&c=message&a=getmessage&start=0&count=10&_=1585033248931))，直接解析json文件即可进一步获得相关评论。

需要用到的库：scrapy, re, urllib, json

## 创建scrapy项目文件

在命令行中创建文件，我们这里使用crawlspider在“shushou.360.cn”中查找相关网页

```
scrapy startproject 360comments
cd 360comments
scrapy genspider -t crawl commentSpider zhushou.360.cn
```



## 设置Item

```python
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
```



## 编写spider文件

1. 导入items模块

```python
from ..items import Comment360Item # 要先导入项目的items模块
```

2. 设置crawlspider的rule

```python
'''
rule规则中allow根据正则表达式书写，匹配到所有带有zhushou.360.cn/detail/index/soft_id/的网页，注意.需要转义;
callback为规则适用的方法，这里follow选择True，代表继续循环执行
'''
rules = (
        Rule(LinkExtractor(allow=r'zhushou\.360\.cn/detail/index/soft_id/\d+'), callback='parse_item', follow=True),
    )
```

3. 编写parse_item方法，返回评论对应的js

```python
item = Comment360Item()
# xpath获取软件名和评分
software = response.xpath('//h2[@id="app-name"]/span/text()').extract_first()
score = response.xpath('//div[@class="pf"]/span[1]/text()').extract_first()
# 注意这里有个坑：xpath获取到的下载量都为0，用正则表达式可以取到
downloadCounts = re.findall('<span class="s-3">下载：(.*?)次</span>', response.text)[0]
# 给item传入数据
item['software'] = software
item['score'] = score
item['downloadCounts'] = downloadCounts
'''
获取评论的链接时spider中最难的一步，在解析网页之后获得了js，访问这个js可以直接获得10条评论
js中有两个需要注意的点：baike以及start，通过baike可以获取具体的app名字以及修饰符，通过start可以实现评论翻页功能
baike可以在script中用正则获取baike_name，start可设置循环传入参数
'''
# 此处要完成拼接url， 获取baike_name
pattern = re.compile("<script>.*?return.*?'baike_name': '(.*?)'.*'?</script>", re.S)
baike_name = re.findall(pattern, response.text)[0]
# print(baike_name)
#调用了urllib.parse中的quote，baike_name转化成网页符号，看起来更整体一点
url = 'https://comment.mobilem.360.cn/comment/getComments?&baike='+ quote(baike_name) + '&start={}&count=10'
for i in range(10):
	full_url = url.format(i)
	if full_url:
	# print(full_url)
    # 利用生成器访问拼接网页，获得详情信息，不过滤网址
    # 这里要注意，要将item继续传入
    yield scrapy.Request(url=full_url, callback=self.parse_detail, meta={'item': item}, dont_filter=True)
```

4. 编写parse_detail方法，获取剩余数据

```python
# 继续往item中添加数据
item = response.meta['item']
# 这里需要注意，scrapy中返回的response是TextResponse格式，要对reponse.body进行解码财能获得字符串格式
json_data = json.loads(response.body.decode())
# 根据字典获取数据
data = json_data['data']
commentCounts = data['total']
item['commentCounts'] = commentCounts
item['comments'] = []
# 在循环内获取每条评论具体信息
for message in data['messages']:
    comments = {}
    comments['pubTime'] = message['create_time']
    comments['userName'] = message['username']
    comments['content']= message['content']
    comments['commentType'] = message['type']
    item['comments'].append(comments)
    yield item
```

![](C:\Users\28499\PycharmProjects\03_scrapy\comment360\评论详情页.png)



## 设定Pipeline

这里选择用mysql保存数据，当然也可以直接在命令端输入以下命令生成json文件：

```
# 这里只选取了一部分进行保存
scrapy crawl commentSpider -o items.json
```

mysql保存方式如下：

```python
# 设置一个num变量，用来记录保存数据条数，navicat有条数，内存限制
num = 1
class Comment360Pipeline(object):
    # 初始化方法，建立连接和游标
    def __init__(self):
        self.conn = pymysql.connect(host="****", user="***", password="***", database="spider_data", port=***, charset="utf8")
        self.cursor = self.conn.cursor()
        print("数据库连接成功")

    def process_item(self, item, spider):
        global num
        sql = """
            insert into 360comments(id, software, score, downloadCounts, commentCounts, userName, pubTime, commentType, content)
            values (null, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # 套用循环，写入数据库
        for i in range(len(item['comments'])):
            print("=="*30)
            print("开始导入第{}条数据".format(num))
            self.cursor.execute(sql, (
            item['software'], item['score'], item['downloadCounts'], item['commentCounts'], item['comments'][i]['userName'],
            item['comments'][i]['pubTime'], item['comments'][i]['commentType'], item['comments'][i]['content']))
            self.conn.commit()
            print("=="*30)
            print("第{}条数据导入完成".format(num))
            num += 1
        return item
	# 关闭游标和数据库
    def close_spider(self, item, spider):
        self.cursor.close()
        self.conn.close()
```



## 中间件

可以不用设置中间件



## settings

```python
# 关闭robots协议
ROBOTSTXT_OBEY = False
# 设定请求头，这个网站反爬虫做的比较简单，就一个ajax，不需要设置代理池
DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/80.0.3987.149 Safari/537.36 '
}
# 开启管道，保存数据
ITEM_PIPELINES = {
   'comment360.pipelines.Comment360Pipeline': 300,
}
```



# @spider部分完整代码

```python
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

```



最后保存了61784条数据

![](C:\Users\28499\PycharmProjects\03_scrapy\comment360\navicat保存数据.png)

之后将对获取到的数据进行分类清洗，做初步数据分析，数据可见csv或xlsx