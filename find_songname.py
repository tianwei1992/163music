from tkinter import *
import tkinter.messagebox as messagebox
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time

class ChooseApp(Tk):
	def __init__(self,song_lst):
		super().__init__()
		self.sonng_lst=song_lst
		self.seq=IntVar()
		self.title('input_sequence')
		self.resizable(1, 0)  # 不懂
		self.setup_UI(song_lst)
	def setup_UI(self,song_lst):
		#self.geometry('300x500')
		# 在root内创建第1行……
		row1 = Frame(self)
		row1.pack(fill="x",side=TOP)
		Label(row1, text='找到相关歌曲'+str(len(song_lst))+'首，请选择：', width=28,font=("黑体", 16, "bold")).pack(side=LEFT)
		#第2行
		row2 = Frame(self)
		row2.pack(fill="x",side=BOTTOM)
		self.r = StringVar()
		#self.r保存选择结果
		for i,song in enumerate(song_lst):
			print(i,song)
			#value是当前选项的特征值
			self.radio = Radiobutton(self, variable=self.r, value=i, text='{0}：{1} by {2}({3})'.format(i,song[1],song[2],song[3]),command=self.sel,activebackground='Lavender',activeforeground='grey',bg='ghostwhite',fg='Black')
			#正常情况下：字体颜色fg，背景色bg
			#选中：字体activeforeground，背景activebackground
			#self.radio.pack(side=LEFT)#所有歌曲排成一行
			self.radio.pack(anchor=W)#锚选项，当可用空间大于所需求的尺寸时，决定组件被放置于容器的何处


		#第三行
		Button(row1, text="取消", command=self.cancel).pack(side=RIGHT)
		Button(row1, text="提交", command=self.ok).pack(side=RIGHT)
		#第4行，
		self.label = Label(self)
		self.label.pack()
	def sel(self):
		selection = "你选择了第{0}首歌".format(str(self.r.get()))
		self.label.config(text=selection)

	def cancel(self):
		self.destroy()
	def ok(self):
		print(self.r.get())
		self.destroy()
		return

def users_choice(song_lst):
	print("请选择:")
	root=ChooseApp(song_lst)
	root.mainloop()
	return int(root.r.get())

#return item
#先假设用户选择了第一个

def find_songname(songname):
	browser = webdriver.Chrome()
	#最小化窗口，因为用户不关心过程
	#browser.minimize_window()报错Message: unknown command: session/67b6fb8a56cad99cc5646646267e71c4/window/minimize
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
	print('调用tk展示song_lst,让用户选择')
	song_seq=users_choice(song_lst)
	print('在tk中，用户选择了：',song_seq)
	song_id = song_lst[song_seq][0]
	return song_id


class InputApp(Tk):
	def __init__(self):
		super().__init__()
		self.song_name = StringVar()
		# 2指定root属性
		self.title('input_songname')
		self.resizable(1, 0)#不懂
		self.geometry('180x60')
		self.setup_UI()
	def setup_UI(self):
	# 3在root内创建第1行……
		row1 = Frame(self)
		row1.pack(fill="x")
		Label(row1, text='请输入歌名：', width=12).pack(side=LEFT)
		Entry(row1, textvariable=self.song_name, width=20).pack(side=LEFT)
	#第2行
		row2 = Frame(self)
		row2.pack(fill="x")
		#这个顺序保证"确定"在左
		Button(row2, text="取消", command=self.cancel).pack(side=RIGHT)
		btn2=Button(row2, text="确定", command=self.ok).pack(side=RIGHT)
	def cancel(self):
		self.destroy()
	def ok(self):
		# 返回输入
		assert self.song_name,"输入为空"
		song_name=self.song_name.get()
		self.destroy()


def input_songname():
	#1创建root主窗口
	root = InputApp()
	root.mainloop()#为什么开两个
	song_name=root.song_name.get()
	return song_name



if __name__=='__main__':
	print('请输入歌名')
	song_name=input_songname()
	#print('用户已输入：',song_name)
	print("下面开始查找相关歌曲")
	song_id=find_songname(song_name)
	print("已经拿到songid,song_id=",song_id)
	#songname='鼓楼'
	#song_id=find_songname(songname)
	#print("with songname='鼓楼',song_id=",song_id)
	#users_choice([[1,2,3,4],[5,6,7,8]])