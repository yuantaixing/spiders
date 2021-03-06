'''
作者: 郑阔
日期: 2018.04.18
版本: 1.0
将 item 写入 mongodb 的 item_pipeline
注意该模块需要在 item_sorter 完成各类信息分类整理后才能调用
因为不同的数据属于不同的 collection,而在数据插入是需要指明 collection
'''
# -*- coding: utf-8 -*-
import datetime
import os
import json

from pymongo import MongoClient

from scrapy.exceptions import NotConfigured


class Item2Mongodb(object):
    '''
    由于该模块设计只包含一个类别,所以功能与模块功能一致
    完成 item 的 mongodb 入库工作
    '''

    def __init__(self, database_config_file):
        '''
        获取数据库的配置信息,初始化数据库连接
        :param self: 类的实例对象
        :param database_config_file: 数据库配置信息文件
        '''
        database_config = json.load(open(database_config_file, 'r'))
        self.mongo_client = MongoClient(database_config['host'], database_config['port'])
        self.database = self.mongo_client[database_config['database']]
        username = database_config['username']
        password = database_config['password']
        if username and password:
            self.connected = self.database.authenticate(username, password)
        else:
            self.connected = True

    @classmethod
    def from_crawler(cls, crawler):
        '''
        主要是从 crawler 当中的 settings 当中获取两个 数据库结构文件的配置信息
        :param cls: 类本身 cls() 相当于调用构造函数 生成类实例
        :param crawler: scrapy 项目运行后的 crawler 实例
        :return: Item2Mongodb 类对象
        :raise: 假如 settings 文件当中没有找到 相应的配置项就会抛出异常
        '''
        # 项目配置信息所在的路径
        config_dir = crawler.settings.get('CONFIG_DIR', None)
        database_config_file = crawler.settings.get('DATABASE_CONFIG', None)
        if not config_dir or not database_config_file:
            raise NotConfigured
        database_config_file = os.path.join(config_dir, database_config_file)
        return cls(database_config_file)

    def open_spider(self, spider):
        """
        爬虫运行前：声明唯一id字段
        :return:
        """
        self.database['content'].create_index('content_id', unique=True)

    def process_item(self, item, spider):
        '''
        完成数据入库
        :param self: 类的对象本身
        :param item: 生成的 item
        :param spider: 传回该 item 的 spider
        :return: 数据库应该是 item 的最后一站,所以 None
        '''
        item['crawl_time'] = datetime.datetime.now()
        item['website_id'] = 'facebook'
        item['website_type'] = 'social'
        self.database['content'].replace_one({'content_id': item['content_id']}, item, upsert=True)
        return item

    def close_spider(self, spider):
        '''
        关闭数据库连接
        :param self: 类的对象实例
        :param spider: spider 实例
        :return: None
        '''
        self.mongo_client.close()
