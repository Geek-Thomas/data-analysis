# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql

num = 1


class Comment360Pipeline(object):

    def __init__(self):
        self.conn = pymysql.connect(host="localhost", user="root", password="1314520", database="spider_data",
                                    port=3306, charset="utf8")
        self.cursor = self.conn.cursor()
        print("数据库连接成功")

    def process_item(self, item, spider):
        global num
        sql = """
            insert into 360comments(id, software, score, downloadCounts, commentCounts, userName, pubTime, commentType, content)
            values (null, %s, %s, %s, %s, %s, %s, %s, %s)
        """
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

    def close_spider(self, item, spider):
        self.cursor.close()
        self.conn.close()
