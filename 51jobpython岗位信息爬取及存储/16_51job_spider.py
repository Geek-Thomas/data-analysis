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
