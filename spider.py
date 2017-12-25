import requests
import json
import os
from Crypto.Cipher import AES
import base64
import codecs
import mysql.connector
#import MySQLdb
from find_songname import get_songid_lst
from tkinter import *
import pynlpir

#以下都是对构造post方法所需data form所用的加密过程，从网上copy而来，不做详解，只用接口
def aesEncrypt(text, secKey):
	pad = 16 - len(text) % 16
	# print(type(text))
	# print(type(pad))
	# print(type(pad * chr(pad)))
	# text = text + str(pad * chr(pad))
	if isinstance(text, bytes):
		# print("type(text)=='bytes'")
		text = text.decode('utf-8')
	# print(type(text))
	text = text + str(pad * chr(pad))
	encryptor = AES.new(secKey, 2, '0102030405060708')
	ciphertext = encryptor.encrypt(text)
	ciphertext = base64.b64encode(ciphertext)
	return ciphertext


def rsaEncrypt(text, pubKey, modulus):
	text = text[::-1]
	#	rs = int(text.encode('hex'), 16)**int(pubKey, 16)%int(modulus, 16)
	rs = int(codecs.encode(text.encode('utf-8'), 'hex_codec'), 16) ** int(pubKey, 16) % int(modulus, 16)
	return format(rs, 'x').zfill(256)

modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
nonce = '0CoJUm6Qyw8W8jud'
pubKey = '010001'

def createSecretKey(size):
	return (''.join(map(lambda xx: (hex(ord(xx))[2:]), str(os.urandom(size)))))[0:16]


def get_it_comments(url):
	#post请求网页，获取歌曲的top100评论，最后以列表形式返回。其中data form由text加密而来
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

	comment_list = []
	count = 0
	for i in range(10):
		# 一个i获取10个评论
		text = {
			'username': '',
			'password': '',
			'rememberLogin': 'true',
			'offset': i * 10
		}
		text = json.dumps(text)
		secKey = createSecretKey(16)
		encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
		encSecKey = rsaEncrypt(secKey, pubKey, modulus)
		payload = {
			'params': encText,
			'encSecKey': encSecKey
		}

		r = requests.post(url, headers=headers, data=payload)
		r.raise_for_status()
		print(r.apparent_encoding)
		r.encoding= r.apparent_encoding
		# print(r.headers)
		print(r.text)

		# 把返回的json格式转换成字典，方便提取关键字
		try:
			r_dic = json.loads(r.text)
		except:
			print("json.loads(r.text)出错了")
		# print(r_dic)
		comments = r_dic["comments"]
		print()
		# print('共有{0}条评论'.format(len(comments)))
		# 与其print不如assert
		assert len(comments) == 10
		for comment in comments:
			comment_list.append([count, comment['content']])
			count += 1
	print('已经get第{0}条评论'.format(len(comment_list)))
	return comment_list


def parse_words(s):
	#调用pynlpir模块分析字符串的关键字及其weight
	pynlpir.open()
	key_words = pynlpir.get_key_words(s, weighted=True)
	pynlpir.close()
	return key_words


def dic2lst(dicc):
	#为对字典元素排序做准备，把字典转换成列表的列表，列表元素也是列表，包含字典的key和value
	lst = []
	for key in dicc:
		lst.append((key, dicc[key]))
	return lst


def get_and_save_top_keywords(songid):
	#对给定songid，爬取评论、解析关键字，并存库
	dic_keywords = {}
	url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + songid + '?csrf_token='
	comments_lst = get_it_comments(url)
	assert comments_lst, 'comments_lst is Null'
	print('爬取部分已经完成')
	for i,comment in comments_lst:
		# print(comment)#[0, '一听就着了迷'
		save_comment(i,comment,songid)
		try:
			key_words = parse_words(comment)
			for key_word in key_words:
				# print(key_word[0], '\t', key_word[1])#雷子 	 6.6
				dic_keywords.update({key_word[0]: dic_keywords.get(key_word[0], 0) + key_word[1]})
		except Exception as e:
			print('comment解析失败：',i,comment)
			print(e)
		else:
			print("comment解析成功:",i,comment)
		finally:
			print()
	print('所有评论的解析与保存已完成')
	#print(sorted(dic2lst(dic_keywords)))
	top_keywords = list(sorted(dic2lst(dic_keywords), key=lambda x: -x[1]))[:10]
	print('下面开始保存top_keywords到数据库')
	try:
		save_to_keywords(songid, top_keywords)
	except Exception as e:
		print("top_keywords保存失败:", top_keywords)
		print(e)
	else:
		print("top_keywords保存成功:", top_keywords)
	return top_keywords


def init_tables():
	#初始化数据库：建立3张表，songs、comments和keywords
	try:
		conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
		# 通常我们在连接MySQL时传入use_unicode=True，让MySQL的DB-API始终返回Unicode
		cursor = conn.cursor()
		cursor.execute('create database if not exists ' + '163music')
		#指定database的CHARACTER SET
		cursor.execute('ALTER DATABASE 163music CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;')
		cursor.execute('use 163music;')

		#创建table songs
		cursor.execute(
			'create table if not exists songs(id TINYINT primary key auto_increment, title varchar(50),singer varchar(50),album varchar(50),songid varchar(10) unique);')

	#创建table comments
		cursor.execute(
			'create table if not exists comments(id INT primary key auto_increment, content text,songid varchar(10),seq tinyint);')
		#指定table的CHARACTER SET 为utf8mb4
		cursor.execute('ALTER TABLE comments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
		#创建表的时候先不指定外键，等修改字符集以后再指定外键

		cursor.execute('alter table comments add constraint comments_fk_songs foreign key(songid) references songs(songid) on delete cascade;')
		cursor.execute(
			'alter table comments add unique index(songid,seq);'
		)
	#添加unique index才能用replace into

		#创建table keywords
		cursor.execute(
			'create table if not exists keywords(id int primary key auto_increment, keyword varchar(20),weight float(5.2),songid varchar(10),seq tinyint);')
		#
		cursor.execute('ALTER TABLE keywords CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
		cursor.execute('alter table keywords add constraint keywords_fk_songs foreign key(songid) references songs(songid) on delete cascade;')
		cursor.execute(
			'alter table keywords add unique index(songid,seq);'
		)
		conn.commit()
		cursor.close()
	except:
		#只有第一次运行时需要执行try的代码。如果不是第一次运行，会发生异常，就让它跳过吧
		pass

def save_comment(i,comment,songid):
	#print(comment_lst,songid)#97 [97, '谢谢'] 447926067
	#charset='utf8mb4'重要，否则emoji保存失败
	conn = mysql.connector.connect(user='root', password='1234', use_unicode=True,charset='utf8mb4')
	cursor = conn.cursor()
	#去掉非法字符，否则入库报错。不过utf8mb4以后，不用下面那样过滤
	#comment=comment.encode('gbk','ignore').decode('gbk')
	#首先默认是对已存在更新，如果更新找不到再insert
	try:
		cursor.execute('replace into 163music.comments(seq,content,songid) values (%s,%s,%s) ',
					   [i, comment, songid])

	except Exception as e:
		print("comment保存失败：", i, comment)

		print(e)
	else:
		print("comment保存成功：", i, comment)
	conn.commit()
	cursor.close()

def save_to_keywords(songid, top_keywords):
	conn = mysql.connector.connect(user='root', password='1234', use_unicode=True,charset='utf8mb4')
	cursor = conn.cursor()
	for i, keyword in enumerate(top_keywords):
		try:
			cursor.execute('replace into 163music.keywords(seq,keyword,weight,songid) values (%s, %s,%s, %s)',
					   [i, keyword[0], keyword[1], songid])

		except:
			print('keyword 保存失败',i,keyword)
		else:
			print('keyword 保存成功！')

	conn.commit()
	cursor.close()


def get_comments_from_db(singer):
	try:
		conn = mysql.connector.connect(user='root', password='1234', use_unicode=True,charset='utf8mb4')
		cursor = conn.cursor()

		cursor.execute(
			'use 163music;'
		)
		cursor.execute(
			'set character_set_results=utf8mb4;'
		)
		query = "select comments.content from comments,songs where comments.songid=songs.songid and songs.singer='{0}';" .format(singer)
		cursor.execute(query)
		comments_lst=list(cursor)
		for i,comment in enumerate(comments_lst):
			print(i,comment[0].encode())
		print("comments查询成功!歌手:{0}，共查到{1}条评论".format(singer,len(comments_lst)))
		return comments_lst
	except Exception as e:
		print('comments查询失败！歌手:{0}'.format(singer))
		print(e)


def calcu_keywords(singer):
	comments_lst=get_comments_from_db(singer)
	#现成的模块包含了每个comment的保存，所以没法复用，这里只能复用parse_words层次
	dic_keywords = {}
	for comment in comments_lst:
		#对每个comment：首先解析出key_words及其weighth,然后把他们加入总字典dic_keywords
		try:
			key_words=parse_words(comment[0])
			#print('key_words==',key_words)#[('没错', 2.0)]
			for key_word in key_words:
				#print(key_word)#('没错', 2.0)
				dic_keywords.update({key_word[0]: dic_keywords.get(key_word[0], 0) + key_word[1]})
			print('当前评论分析成功',comment[0])
		except Exception as e:
			print('当前评论分析失败',comment)
			print(e)
	#print('dic_keywords=',dic_keywords)
	return (dic_keywords)


seq_selected = []
def choose_process():
	#启动程序，选择process
	print("请选择:")
	root=Tk()
	#第1行
	row1 = Frame(root)
	row1.pack(fill="x", side=TOP)
	Label(row1, text='想做做点什么？', width=40, font=("宋体", 16, "bold")).pack(side=LEFT)
	#第2行
	scrollbar = Scrollbar(root,orient = VERTICAL)
	scrollbar.pack(side=LEFT,fill=Y)
	mylist = Listbox(root, yscrollcommand=scrollbar.set, selectmode=MULTIPLE,width=80)
	process_lst=['爬取新歌','查询歌手关键词']
	for i, process in enumerate(process_lst):
		mylist.insert(END, '{0}：{1}'.format(i, process))
	mylist.pack(side=LEFT, fill=X)
	scrollbar.config(command=mylist.yview)

	#第3行
	def cancel():
		root.destroy()
	def ok():
		global seq_selected
		seq_selected = mylist.curselection()
		root.destroy()

	button1=Button(row1, text="取消", command=cancel).pack(side=RIGHT)
	button2=Button(row1, text="提交", command=ok).pack(side=RIGHT)
	root.mainloop()
	return


def new_crawl():
	# 0 开始新的爬取
	print("下面载数据库中新建3张表")
	init_tables()
	print("下面开始主流程")
	#songname='鼓楼'
	songs_selected=get_songid_lst()
	print('下面开始一首一首获取评论')
	for song_selected in songs_selected:
		#song_selected是一个list，依次包含songid,title,singer,album
		song_id=song_selected[0]
		print("下面开始对id为{0}的歌进行爬取和分析".format(song_id)   )
		top_keywords = get_and_save_top_keywords(song_id)
		assert top_keywords, 'top_keywords is Null'
		for i, top_keyword in enumerate(top_keywords):
			print('top{0}\t{1}\t{2}'.format(i, top_keyword[0], top_keyword[1]))

def get_singers_from_db():
	#1 从数据库历史信息中分析某歌手的关键词
	try:
		conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
		# 通常我们在连接MySQL时传入use_unicode=True，让MySQL的DB-API始终返回Unicode
		cursor = conn.cursor()
		cursor.execute(
			'use 163music;'
		)
		cursor.execute(
			'use 163music;'
		)

		query = "select distinct singer from songs "
		cursor.execute(query)
		singer_lst=list(cursor)
		for i,singer in enumerate(singer_lst):
			print(i,singer)
		print("comments查询成功!数据库当前共有{0}位歌手".format(len(singer_lst)))
		return singer_lst
	except Exception as e:
		print('comments查询失败！歌手:{0}'.format(singer))
		print(e)

def choose_one_singer(singer_lst):
	#从singer_lst中选择其中一位
	print("请选择:")
	root = Tk()
	# 第1行
	row1 = Frame(root)
	row1.pack(fill="x", side=TOP)
	Label(row1, text='选择要查询的歌手', width=40, font=("宋体", 16, "bold")).pack(side=LEFT)
	# 第2行
	scrollbar = Scrollbar(root, orient=VERTICAL)
	scrollbar.pack(side=LEFT, fill=Y)
	mylist = Listbox(root, yscrollcommand=scrollbar.set, selectmode=MULTIPLE, width=80)
	process_lst = ['爬取新歌', '查询歌手关键词']
	for i, singer in enumerate(singer_lst):
		mylist.insert(END, '{0}：{1}'.format(i, singer))
	mylist.pack(side=LEFT, fill=X)
	scrollbar.config(command=mylist.yview)

	# 第3行
	def cancel():
		root.destroy()

	def ok():
		global seq_selected
		seq_selected = mylist.curselection()
		root.destroy()

	button1 = Button(row1, text="取消", command=cancel).pack(side=RIGHT)
	button2 = Button(row1, text="提交", command=ok).pack(side=RIGHT)
	root.mainloop()
	return


def choose_singer():
	singers=get_singers_from_db()
	choose_one_singer(singers)
	singer_selected = seq_selected
	return singer_selected

def read_past():
	#来一个弹窗输入singer
	singer=choose_singer()
	singer='赵雷'
	dic_keywords=calcu_keywords(singer)
	top_keywords = list(sorted(dic2lst(dic_keywords), key=lambda x: -x[1]))[:10]
	for top_keyword in top_keywords:
		print(top_keyword)


if __name__ == '__main__':
	choose_process()
	#程序启动，先选择执行新的爬取还是分析历史评论，还是都要
	for seq in seq_selected:
		if seq==0:
			print('0 执行新的爬取')
			new_crawl()
		if seq==1:
			print('1 分析历史评论')
			read_past()