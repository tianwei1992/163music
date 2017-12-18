from tkinter import *
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time


"""
还是用正则，这种方式拿不到songid
print('key_infos========',type(key_infos.text))#str
print('key_infos========', key_infos.text.split("\n"))

info_lst=key_infos.text.split("\n")

song_lst=[]
for i in range(len(info_lst)):
	if i%4==0:
		song_dic={}
		song_dic['name']=info_lst[i]
	elif i % 4 == 1:
		song_dic['singer']=info_lst[i]
	elif i % 4 == 2:
		song_dic['album']=info_lst[i]
	else:
		song_dic['lenth']=info_lst[i]
		song_lst.append(song_dic)
print(song_lst)
"""


#要把这个list用tk给用户看，用户选择其中的某一个
def users_choice(song_lst):
	return 1

#return item
#先假设用户选择了第一个

def find_songname(songname):
	browser = webdriver.Chrome()
	url = 'http://music.163.com/#/search/m/'
	browser.get(url)
	#先定位到g-iframe这个frame
	frame1 = browser.find_element_by_css_selector(".g-iframe")
	browser.switch_to.frame(frame1)
	# 再定位到输入框，输入songname
	browser.find_element_by_id("m-search-input").send_keys(songname)
	#再定位到搜索按钮，点击
	browser.find_element_by_css_selector(".btn").click()
	# 必须等待，否则网页还没开始加载
	WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_class_name("srchsongst"))
	#拿到渲染后的网页，
	text = browser.page_source
	browser.close()
	#print(text)
	#用正则提取歌曲信息，保存到song_lst
	pat = re.compile(
		r'<div cla.*?song_(.*?)" cla.*?b title="(.*?)">.*?artist.*?>(.*?)</a>.*?album.*?le="(.*?)">.*?</div>')
	# pat=r'<div class="item.*?<a id="song_(.*?)" class="ply.*?><b title="(.*?).*?artist?id=.*?>(.*?)</a></div>.*?title="(.*?).*?</div></div>'
	song_lst = pat.findall(text, re.S)
	print('展示相关歌曲{0}首'.format(len(song_lst)))
	for song in song_lst:
		print(song)
	#呈现给用户，让用户选择
	song_seq=users_choice(song_lst)
	song_id = song_lst[song_seq][0]
	return song_id


if __name__=='__main__':
	songname='路口'
	song_id=find_songname(songname)
	print("with songname='路口',song_id=",song_id)
	songname='鼓楼'
	song_id=find_songname(songname)
	print("with songname='鼓楼',song_id=",song_id)