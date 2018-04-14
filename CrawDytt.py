#!/usr/bin/python
# coding=utf-8
import re
import threading
import os
from bs4 import BeautifulSoup
import requests
import traceback

starturl = "http://www.ygdy8.com"


class myThread (threading.Thread):  # 继承父类threading.Thread
    def __init__(self, url, dir):
        threading.Thread.__init__(self)
        self.url = url
        self.dir = dir

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        CrawListPage(self.url, self.dir)


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


def CrawIndexPage(starturl, html):
    soup = BeautifulSoup(html, "html.parser")
    res = soup.find_all(id='menu')[0]
    for menu in res.find_all("a")[:-2]:
        urlList = []
        try:
            child_url = starturl + menu.get("href")
            catalog = menu.text
            dir = "/home/allen/Craw/movie/" + catalog
            if os.path.isdir(dir):
                pass
            else:
                os.mkdir(dir)
                print("创建分类目录成功------"+dir)

            thread = myThread(child_url, dir)
            thread.start()
        except:
            traceback.print_exc()
            continue


def CrawListPage(child_url, dir):
    html = getHTML(child_url)
    soup = BeautifulSoup(html, "html.parser")
    try:
        pages = (int(soup.find_all("option")
                     [-1].text), soup.find_all("option")[-1].get("value"))
        print(pages)
        li = pages[1].split('_')
        # print(li)
        newurl = child_url.replace(
            'index.html', li[0] + '_' + li[1] + '_1.html')
        print(newurl)
        for i in range(1, pages[0]):
            li = newurl.split('_')
            # print(li)
            pageurl = li[0] + "_" + li[1] + '_'+str(i) + ".html"
            print("******第"+str(i)+"页******", pageurl)
            html_1 = getHTML(pageurl)
            soup_1 = BeautifulSoup(html_1, "html.parser")
            for res in soup_1.find_all(attrs={"class": "ulink"}):
                sourceurl = starturl + res.get("href")
                # with open(dir+'/'+res.text, "w") as f:
                # f.write(sourceurl)

                print(res.text)
                CrawSourcePage(sourceurl, dir, res.text)
    except:
        pass
        traceback.print_exc()


def CrawSourcePage(url, dir, filename):
    # print(url)
    try:
        html = getHTML(url)
        sources = re.findall(r'"ftp://.*"', html)
        for source in sources:
            # filename = source[:-4].split('/')[-1].replace(".", "")
            s = dir + "/" + filename + ".txt"
            print(s)
            with open(s, "a+") as f:
                f.write(source+"\n")
                # print("ok")

    except:
        traceback.print_exc()
        pass


def main():

    html = getHTML(starturl)
    CrawIndexPage(starturl, html)
    # dir = "/home/allen/Craw/movie/"
    # CrawSourcePage('http://www.ygdy8.com/html/gndy/jddy/20180115/56096.html', dir)
    # CrawListPage("http://www.ygdy8.com/html/gndy/dyzz/index.html",
    #         dir)


main()
