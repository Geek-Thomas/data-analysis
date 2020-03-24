# 爬取51job岗位信息

爬取思路：

通过url获取页面信息，xpath获取每页中详情页url，访问详情页，解析页面获得岗位信息。本次爬取对象为python+上海 岗位，最后将岗位信息保存到mysql中

需用到的库：requests(网络请求), lxml(解析网页),tim(设置休眠),pymysql(将数据保存至mysql) 

通过以下几个函数实现：



## 1.get_detail_page(获取页面url)

通过访问51job页面，获取页面中招聘信息url

```python
def get_detail_page(url):
    response = requests.get(url, headers=headers)
    text = response.text
    html = etree.HTML(text)
    urls = html.xpath('//div[@class="el"]//a[@target="_blank"]/@href')
    #防止访问过于频繁
    time.sleep(1)
    position_list = []
    for detail_url in urls:
        #调用parse_detail_url函数
        position_list.append(parse_detail_page(detail_url))
```



## 2.parse_detail_url(解析详情页url)

解析详情页，用字典保存数据

```python
def parse_detail_page(url):
    response = requests.get(url, headers=headers)
    #可在网页element中搜索charset元素，网页编码为gbk
    text = response.content.decode('gbk')
    html = etree.HTML(text)
    #对xpath获取数据进行处理，将列表变量转化为规整的字符型
    company = "".join(html.xpath('//p[@class="cname"]/a/@title'))
    positionName = "".join(html.xpath('//div[@class="in"]//h1/@title'))
    job_request = html.xpath('//div[@class="in"]//p[@class="msg ltype"]/text()')
    job_request = ",".join([i.strip() for i in job_request])
    welfare = ",".join(html.xpath('//div[@class="t1"]/span/text()')).strip()
    job_description = "".join(html.xpath('//div[@class="tBorderTop_box"]/div[@class="bmsg job_msg inbox"]/p//text()')).strip()
    adress = "".join(html.xpath('//div[@class="bmsg inbox"]/p/text()'))
    if company:
        #当取到了company时才生成岗位字典
        position = {
            "公司": company,
            "岗位": positionName,
            "福利": welfare,
            "职位要求": job_request,
            "职位信息": job_description,
            "上班地址": adress
        }
        #将字典中数据保存到mysql
        save_to_mysql(position)
        print("successfully imported")
    else:
        pass
    time.sleep(1)

```



## 3.save_to_mysql(将数据保存到mysql中)

该函数涉及以下几个功能：

1.在spider_data中新建数据表 data_sets；

2.设置数据表内容(其中id为自动增加的主键元素)；

3.传入字典数据，保存至数据库

```python
def save_to_mysql(data):
    conn = pymysql.connect(host="localhost", user="root", database="spider_data", password="***", port=***)
    cursor = conn.cursor()
    #新建数据库data_sets
    # sql = """
    #         CREATE TABLE data_sets (
    #         id int not null auto_increment,
    #         company VARCHAR(255) not null,
    #         job VARCHAR(255) not null,
    #         welfare VARCHAR(255) not null,
    #         requirements VARCHAR(255) not null,
    #         description VARCHAR(255) not null,
    #         workplace VARCHAR(255) not null,
    #         primary key(id)
    #         )
    #         """
    # cursor.execute (sql)

    try:
        sql = """
         insert into data_sets(company, job, welfare, requirements, description, workplace) values(%s, %s, %s, %s, %s, %s)
            """
        company = data['公司']
        job = data['岗位']
        welfare = data['福利']
        requirements = data['职位要求']
        description = data['职位信息']
        workplace = data['上班地址']

        cursor.execute(sql, (company, job, welfare, requirements, description, workplace))
        conn.commit()
        conn.close()
    except TypeError and pymysql.err.DataError:
        pass
```

问题：新建数据库data_sets不能重复执行，在执行完第一次(即"successfully imported"打印一次后，即需要中断程序)



## 4.主函数负责程序运行

页面翻页存在明显规律，故设置一个循环实现翻页功能，在主函数中调用最重要的parse_detail_url以及save_to_mysql函数

```python
def main():
    url = "https://search.51job.com/list/020000,000000,0000,00,9,99,Python,2," \
          "{}.html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=0" \
          "&dibiaoid=0&line=&welfare= "
    for i in range(1, 133):
        try:
            data = get_detail_page(url.format(i))
        except UnicodeDecodeError:
            pass
```



# 完整代码

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: Thomas. Luo 
# time: 2020/3/18
import requests
from lxml import etree
import time
import pymysql

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/80.0.3987.132 Safari/537.36'
}


def get_detail_page(url):
    response = requests.get(url, headers=headers)
    text = response.text
    html = etree.HTML(text)
    urls = html.xpath('//div[@class="el"]//a[@target="_blank"]/@href')
    time.sleep(1)
    position_list = []
    for detail_url in urls:
        position_list.append(parse_detail_page(detail_url))
    # print(position_list)
    return position_list


def parse_detail_page(url):
    response = requests.get(url, headers=headers)
    text = response.content.decode('gbk')
    html = etree.HTML(text)
    company = "".join(html.xpath('//p[@class="cname"]/a/@title'))
    positionName = "".join(html.xpath('//div[@class="in"]//h1/@title'))
    job_request = html.xpath('//div[@class="in"]//p[@class="msg ltype"]/text()')
    job_request = ",".join([i.strip() for i in job_request])
    welfare = ",".join(html.xpath('//div[@class="t1"]/span/text()')).strip()
    job_description = "".join(html.xpath('//div[@class="tBorderTop_box"]/div[@class="bmsg job_msg inbox"]/p//text()')).strip()
    adress = "".join(html.xpath('//div[@class="bmsg inbox"]/p/text()'))
    if company:
        position = {
            "公司": company,
            "岗位": positionName,
            "福利": welfare,
            "职位要求": job_request,
            "职位信息": job_description,
            "上班地址": adress
        }
        save_to_mysql(position)
        print("successfully imported")
    else:
        pass
    time.sleep(1)


def save_to_mysql(data):
    conn = pymysql.connect(host="localhost", user="root", database="spider_data", password="1314520", port=3306)
    cursor = conn.cursor()
    #及时终止程序
    # sql = """
    #         CREATE TABLE data_sets (
    #         id int not null auto_increment,
    #         company VARCHAR(255) not null,
    #         job VARCHAR(255) not null,
    #         welfare VARCHAR(255) not null,
    #         requirements VARCHAR(255) not null,
    #         description VARCHAR(255) not null,
    #         workplace VARCHAR(255) not null,
    #         primary key(id)
    #         )
    #         """
    # cursor.execute (sql)

    try:
        sql = """
         insert into data_sets(company, job, welfare, requirements, description, workplace) values(%s, %s, %s, %s, %s, %s)
            """
        company = data['公司']
        job = data['岗位']
        welfare = data['福利']
        requirements = data['职位要求']
        description = data['职位信息']
        workplace = data['上班地址']

        cursor.execute(sql, (company, job, welfare, requirements, description, workplace))
        conn.commit()
        conn.close()
    except TypeError and pymysql.err.DataError:
        pass


def main():
    url = "https://search.51job.com/list/020000,000000,0000,00,9,99,Python,2," \
          "{}.html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=0" \
          "&dibiaoid=0&line=&welfare= "
    # data = []
    for i in range(1, 133):
        try:
            # get_detail_page(url.format(i))
            data = get_detail_page(url.format(i))
        except UnicodeDecodeError:
            pass
    # print(data)


if __name__ == '__main__':
    main()

```

