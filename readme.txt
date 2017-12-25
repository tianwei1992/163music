2017.12.24
1、有用文件有2个：
（1）spider.py#主流程从这里开始
（2）find_songname.py#功能模块，实现把song_name转换成song_id，被spider.py引入

2、实现的功能
（1）GUI界面显示数据库查询结果（歌手或者歌曲），供用户选择，支持单选和多选
（2）对指定歌名的歌曲，联网爬取歌曲信息，获得top100评论，并解析出top10关键词,分别保存至数据库相应的表（songs、comments和keywords）。支持emoji表情保存
（3）对指定人名的歌手，取出库中保存的关联歌曲评论，解析出该歌手的评论关键词并展示
（4)


3、用到的模块
（1）网页爬取相关
import requests
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import os

（2）加密算法相关
from Crypto.Cipher import AES
import base64
import codecs
（3)数据库操作相关
import mysql.connector
#import MySQLdb
（4）GUI相关
from tkinter import *
import tkinter.messagebox as messagebox
（5）汉语分词解析
import pynlpir


3、简易使用手册：
（1）运行spider.py，选择process，支持单选和多选
0 输入歌名爬取新歌曲
1 从历史库分析歌手关键词

（1）.0输入歌名爬取新歌曲：
首先出现GUI提示输入歌曲名称，输入后自动搜索相关歌曲并GUI列表展示，选择其中需感兴趣的歌曲（支持单选和多选），自动完成评论爬取和关键词解析，结果保存到数据库，并同步展示在console台。

（1）.1从历史库分析歌手关键词

首先出现GUI展示数据库中所有歌手名称，共用户选择，支持单选和多选。用户做出选择后，自动搜索数据库中当前保存的该歌手演唱歌曲的评论，自动完成top10关键词解析并展示。


4、值得注意的的问题和代码

（1）find_songname.py中，构造了继承自Tk的自定类class InputApp(Tk)，然后在input_songname()中，生成了InputApp的一个实例，执行mainloop即可实现歌曲名的输入 （这段代码还要细看）.其余实现选择功能的的GUI都是派生自Tk，代码也是一个模板。

（2）find_songname.py中，webdriver两次用到等待，这很有必要：
WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_class_name("g-iframe"))和WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_class_name("srchsongst"))

（3）find_songname.py中，webdriver对html元素的定位，需要首先browser.switch_to.frame(frame1)定位到某个frame，下一句再去查找其中的css元素，否则找不到。

（4）spider.py中，加密相关模块是从网上copy的，待理解。

（5)善用assert，比print更直观，例如 assert len(comments) == 10

（6）如果字典的value都是数字，如何将字典元素按value大小排序？
首先需要构造lst=dic2lst(dicc),接着top_keywords = list(sorted(dic2lst(dic_keywords), key=lambda x: -x[1]))[:10],从关键词字典找出top10的关键词

（7）数据库中建表时，指定合适的字段类型、外键、唯一索引。

（8）为了成功保存emoji表情，指定database和table的CHARACTER SET 为utf8bm4编码，且连接数据库时也要指定utf8bm4编码。conn = mysql.connector.connect(user='root', password='1234', use_unicode=True,charset='utf8mb4')

（9）数据库插入数据时，根据情况决定是新增insert还是更新update。为了改insert into为replace into，同时配合增加songid+seq两个字段联合构成的unique key作为查重条件。
