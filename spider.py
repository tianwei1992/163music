import requests
import json
import os
from Crypto.Cipher import AES
import base64
import codecs
import mysql.connector
#import MySQLdb
import find_songname


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
		# print(r.headers)
		# print(r.text)
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
			# print(comment)
			comment_list.append([count, comment['content']])
			count += 1
		# 也可用正则取出评论的nickname和content
	print('已经get第{0}条评论'.format(len(comment_list)))
	return comment_list


import pynlpir


def parse_words(s):
	pynlpir.open()
	#print(type(s))#<class 'str'>
	print(s)
	key_words = pynlpir.get_key_words(s, weighted=True)
	pynlpir.close()
	return key_words


def dic2lst(dicc):
	lst = []
	for key in dicc:
		lst.append((key, dicc[key]))
	return lst



def get_and_save_top_keywords(songid):
	dic_keywords = {}
	url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + songid + '?csrf_token='
	comments_lst = get_it_comments(url)
	assert comments_lst, 'comments_lst is Null'
	print('爬取部分已经完成')
	for i,comment in comments_lst:
		# print(comment)#[0, '一听就着了迷'
		try:
			save_comment(i,comment,songid)
		except Exception as e:
			print("comment保存失败：", i,comment)
			print(e)
		else:
			print("comment保存成功：",i, comment)
		# 保存的同时当场解析

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
	print(sorted(dic2lst(dic_keywords)))
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
	conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
	# 通常我们在连接MySQL时传入use_unicode=True，让MySQL的DB-API始终返回Unicode
	cursor = conn.cursor()
	cursor.execute('create database if not exists ' + '163music')
	cursor.execute(
		'create table if not exists 163music.songs(id TINYINT primary key auto_increment, title varchar(50),singer varchar(50),album varchar(50),songid varchar(10) unique);')

	cursor.execute(
		'create table if not exists 163music.comments(id INT primary key auto_increment, content varchar(500),songid varchar(10),seq tinyint,foreign key(songid) references 163music.songs(songid) on delete cascade);')
	cursor.execute(
		'alter table 163music.comments add unique index(songid,seq);'
	)

	cursor.execute(
		'create table if not exists 163music.keywords(id int primary key auto_increment, keyword varchar(20),weight float(5.2),songid varchar(10),seq tinyint,foreign key(songid) references 163music.songs(songid) on delete cascade);')
	cursor.execute(
		'alter table 163music.keywords add unique index(songid,seq);'
	)
	cursor.execute(
		'use 163music;'
	)
	mysql_set_charset('utf8mb4');

	conn.commit()
	cursor.close()


def save_comment(i,comment,songid):
	#print(comment_lst,songid)#97 [97, '谢谢'] 447926067
	# 后面再加，如果有其他songid，insert；如果是一个songid第二次运行，update
	conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
	# 通常我们在连接MySQL时传入use_unicode=True，让MySQL的DB-API始终返回Unicode
	cursor = conn.cursor()
	#去掉非法字符，否则入库报错
	comment=comment.encode('gbk','ignore').decode('gbk')
	#首先默认是对已存在更新，如果更新找不到再insert
	try:
		cursor.execute('replace into 163music.comments(seq,content,songid) values (%s,%s,%s) ',
					   [i, comment, songid])

	except:
		print("comment保存失败：", i, comment)
		#cursor.execute('update 163music.comments set content=%s where songid=%s and seq=%s',
#					   [comment, songid, i])
	else:
		print("comment保存成功：", i, comment)
	conn.commit()
	cursor.close()

def save_to_keywords(songid, top_keywords):
	conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
	# 通常我们在连接MySQL时传入use_unicode=True，让MySQL的DB-API始终返回Unicode
	cursor = conn.cursor()
	for i, keyword in enumerate(top_keywords):
		try:
			cursor.execute('replace into 163music.keywords(seq,keyword,weight,songid) values (%s, %s,%s, %s)',
					   [i, keyword[0], keyword[1], songid])

		except:
			print('keyword 保存失败',i,keyword)
			#cursor.execute('update 163music.keywords set keyword=%s,weight=%s where songid=%s and seq=%s',
#						   [keyword[0], keyword[1], songid, i])

		else:
			print('keyword 保存成功！')

	conn.commit()
	cursor.close()


def get_songid_by_name(songname):
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
	for i in range(10):
		# 一个i获取10个评论
		text = {
			'username': '',
			'password': '',
			'rememberLogin': 'true',
			'keywords':songname
		}
		text = json.dumps(text)
		secKey = createSecretKey(16)
		encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
		encSecKey = rsaEncrypt(secKey, pubKey, modulus)
		payload = {
			'params': encText,
			'encSecKey': encSecKey
		}
		url='http://music.163.com/weapi/search/suggest/web?csrf_token='
		r = requests.post(url, headers=headers, data=payload)
		r.raise_for_status()
		print(r.headers)
		print(r.text)
		# 把返回的json格式转换成字典，方便提取关键字

		try:
			r_dic = json.loads(r.text)
		except:
			print("json.loads(r.text)出错了")
		print(r_dic)
		#comments = r_dic["comments"]
		print()


def get_comments_from_db(singer):
	try:
		conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
		# 通常我们在连接MySQL时传入use_unicode=True，让MySQL的DB-API始终返回Unicode
		cursor = conn.cursor()
		cursor.execute(
			'use 163music;'
		)
		query = "select comments.content from comments,songs where comments.songid=songs.songid and songs.singer='{0}';" .format(singer)
		cursor.execute(query)
		comments_lst=list(cursor)
		for i,comment in enumerate(comments_lst):
			print(i,comment)
		print("comments查询成功!歌手:{0}，共查到{1}条评论".format(singer,len(comments_lst)))
		return comments_lst
	except Exception as e:
		print('comments查询失败！歌手:{0}'.format(singer))
		print(e)



def calcu_keywords(singer):
	comments_lst=get_comments_from_db(singer)
	#直接调用现成的模块，不需要自己再写
	dic_keywords = {}
	for comment in comments_lst:
		#对每个comment：首先解析出key_words及其weighth,然后把他们加入总字典dic_keywords
		try:
			key_words=parse_words(comment[0])
			print('key_words==',key_words)#[('没错', 2.0)]
			for key_word in key_words:
				#print(key_word)#('没错', 2.0)
				dic_keywords.update({key_word[0]: dic_keywords.get(key_word[0], 0) + key_word[1]})
			print('当前评论分析成功',comment[0])
		except Exception as e:
			print('当前评论分析失败',comment)
			print(e)
	#print('dic_keywords=',dic_keywords)
	return (dic_keywords)


if __name__ == '__main__':
	"""
	# 在数据库中新建两张表，comments和keywords
	print("下面载数据库中新建3张表")
	init_tables()
	print("下面开始主流程")
	#songname='鼓楼'
	songs_selected=find_songname.get_songid_lst()
	print('下面开始一首一首获取评论')
	for song_selected in songs_selected:
		#song_selected是一个list，依次包含songid,title,singer,album
		song_id=song_selected[0]
		print("下面开始对id为{0}的歌进行爬取和分析".format(song_id)   )
		top_keywords = get_and_save_top_keywords(song_id)
		assert top_keywords, 'top_keywords is Null'
		for i, top_keyword in enumerate(top_keywords):
			print('top{0}\t{1}\t{2}'.format(i, top_keyword[0], top_keyword[1]))
		"""
	dic_keywords=calcu_keywords('赵雷')
	top_keywords = list(sorted(dic2lst(dic_keywords), key=lambda x: -x[1]))[:10]
	for top_keyword in top_keywords:
		print(top_keyword)

