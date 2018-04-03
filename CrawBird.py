#!/usr/bin/python
# coding=utf-8
import re
import threading
import os
from bs4 import BeautifulSoup
import requests
import traceback

basic_url = "http://www.birdnet.cn/"
name = ''
dir = "/home/allen/Craw/pic/"


class myThread (threading.Thread):  # 继承父类threading.Thread
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.url = url
#        self.num = num

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        DowloadPic(self.url)


def getHTML(url):
    try:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        r.encoding = "gb2312"
        html = r.text
        return html
    except:
        return ""


def getPic(url):
    try:
        pic_list = []
        html = getHTML(url)
        bs = BeautifulSoup(html, 'html.parser')
        shells = bs.find_all('ignore_js_op')
        for shell in shells:
            contents = shell.find_all('img')
            for content in contents:
                try:
                    con = content['file']
                    url = basic_url+con
#                    thread = myThread(url)
 #                   thread.start()
                    DowloadPic(url)
                    print(url)
                    #DowloadPic(url, num)
                except:
                    pass

    except:
        traceback.print_exc()
        pass


def DowloadPic(url):
    try:

        #        num = open(dir+'page.txt', 'r').read()
        #       print(num)
        #        filename = name+"_0"+str(num)+".jpg"

        if os.path.isdir(dir+name):
            pass
        else:
            os.mkdir(dir+name)
            open(dir+name+"/"+'page.txt', 'w').write('1')

        num = open(dir+name+'/'+'page.txt', 'r').read()
        filename = name+"_0"+str(num)+'.jpg'

        ir = requests.get(url)
        if ir.status_code == 200:
            if os.path.exists(dir+name+'/'+filename):
                print("文件已经存在！")
                pass
            else:
                open(dir+name+'/'+filename, 'wb').write(ir.content)
                print("第"+num+"张图片............" + "ok.\n")
                num = int(num)
                num += 1
        open(dir+name+"/"+'page.txt', 'w').write(str(num))

    except:
        traceback.print_exc()
        pass


def getPage(url):
    page_list = []
    html = getHTML(url)
    print(url)
    soup = BeautifulSoup(html, "html.parser")
    for href in soup.find_all(href=re.compile(r"^forum.php\?mod=viewthread")):
        bs = href["href"]
        page_list.append(basic_url+bs)
    return page_list


def main():
    n = 3
    url = input("请输入要爬取的url地址：")
    global name
    name = input("英文名称：")
    for i in range(n):
        url = url + str(i)
        pages = getPage(url)
        for page in pages:
            print("正在爬取:", page)
            getPic(page)


main()
