from tkinter import *
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import mysql.connector


#定义全局变量seq_selected，用于保存用户选择
seq_selected = []
def users_choice(song_lst):
	print("请选择:")
	root=Tk()
	#第1行
	row1 = Frame(root)
	row1.pack(fill="x", side=TOP)
	Label(row1, text='找到相关歌曲' + str(len(song_lst)) + '首，请选择：', width=40, font=("宋体", 16, "bold")).pack(side=LEFT)
	#第2行
	#Scrollbar+Listbox
	scrollbar = Scrollbar(root,orient = VERTICAL)
	scrollbar.pack(side=LEFT,fill=Y)
	mylist = Listbox(root, yscrollcommand=scrollbar.set, selectmode=MULTIPLE,width=80)
	for i, song in enumerate(song_lst):
		mylist.insert(END, '{0}：{1} by {2} ({3})'.format(i, song[1], song[2], song[3]))
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
	#没有返回

def find_songname(songname):
	#用selenium定位输入框，避免了构造用于post的dataform
	browser = webdriver.Chrome()
	url = 'http://music.163.com/#/search/m/'
	browser.get(url)
	#加入等待，免得网速原因导致加载缓慢时报异常
	WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_class_name("g-iframe"))
	#先切换到class=g-iframe这个frame，才能进一步定位到其中的元素
	frame1 = browser.find_element_by_css_selector(".g-iframe")
	browser.switch_to.frame(frame1)
	# 定位到输入框，输入songname
	browser.find_element_by_id("m-search-input").send_keys(songname)
	#定位到搜索按钮，click
	browser.find_element_by_css_selector(".btn").click()
	# 再次等待页面加载和渲染完毕
	WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_class_name("srchsongst"))
	#拿到渲染后的网页html代码，保存至text
	text = browser.page_source
	browser.close()
	#构造正则，用于从text中提取歌曲信息，保存到song_lst
	#歌曲信息包括songid+title+singer+album
	pat = re.compile(
		r'<div cla.*?song_(.*?)" cla.*?b title="(.*?)">.*?artist.*?\d+">([^<][^s].*?)</.*?album.*?le="(.*?)">.*?</div>')
	# pat=r'<div class="item.*?<a id="song_(.*?)" class="ply.*?><b title="(.*?).*?artist?id=.*?>([^s].*?)</a></div>.*?title="(.*?).*?</div></div>'
	song_lst = pat.findall(text, re.S)
	print('展示相关歌曲{0}首'.format(len(song_lst)))
	for song in song_lst:
		print(song)
	#调用tk呈现给用户，让用户选择
	print('调用tk展示song_lst,让用户选择')
	users_choice(song_lst)
	#拿到用户选择序号
	print('在tk中，用户选择了：',seq_selected)
	#从所选序号还原出完整歌曲信息，返回
	songs_selected=[]
	for seq in seq_selected:
		#返回songid+title+singer+album
		songs_selected.append([song_lst[seq][0],song_lst[seq][1],song_lst[seq][2],song_lst[seq][3]])
	return songs_selected


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
	#调用tk窗口，供用户输入歌曲名，保存至song_name返回
	root = InputApp()
	root.mainloop()
	song_name=root.song_name.get()
	return song_name

def save_to_songs(song_list):
	#把歌曲信息保存到数据库songs表
	conn = mysql.connector.connect(user='root', password='1234', use_unicode=True)
	cursor = conn.cursor()
	for song in song_list:
		print(song)
		try:
			cursor.execute('insert into 163music.songs(songid,title,singer,album) values (%s, %s,%s, %s)',
					   [song[0], song[1], song[2], song[3]])
		except Exception as e:
			print('songs保存失败',song)
			print(e)
	conn.commit()
	cursor.close()


def get_songid_lst():
	print('请输入歌名')
	song_name = input_songname()
	print('用户已输入：', song_name)
	print("下面开始查找相关歌曲")
	songs_selected = find_songname(song_name)
	assert len(songs_selected), '用户没有选择，请重新启动'
	print("用户已选择{0}项，下面保存至songs表……".format(len(songs_selected)))
	save_to_songs(songs_selected)
	print('songs保存成功！')
	for song_selected in songs_selected:
		print(song_selected[0])
	return songs_selected


if __name__=='__main__':
	#启动本模块的主流程，可以遍历本模块的所有函数
	get_songid_lst()