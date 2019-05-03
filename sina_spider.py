# -*-coding:utf-8 -*-
from __future__ import print_function
from bs4 import BeautifulSoup
from sqlutil import sqlutil
import requests
import time as ti

'''
Created on 2016年7月17日
新浪新闻关于自贸区的内容
@author: Cesar
'''

start_page = 54


def start():
    base_url = 'http://search.sina.com.cn/'
    first_url = "?q=%D7%D4%C3%B3%C7%F8&c=news&from=index&" \
                "col=&range=&source=&country=&size=&time=&a=&page=" + str(start_page) + "&pf=2131425452&" \
                                                                                        "ps=2134309112&dpc=1"
    headers = {'User-Agent': "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11"}
    i = start_page - 1
    url = base_url + first_url
    while True:
        try:
            i += 1
            print('第' + str(i) + '页：')
            # 获取页面源码
            html = requests.get(url, headers=headers).text
            soup = BeautifulSoup(html, "html.parser")
            infos = soup.find_all("div", {"class": "r-info r-info2"})
            for info in infos:
                href = info.find("a").get('href')
                title = ""
                for s in info.find("a").stripped_strings:
                    title += s
                source_time = info.find("span", {"class": "fgray_time"}).string.split(" ")
                source = source_time[0]
                time = source_time[1] + ' ' + source_time[2]
                sqlutil.insert_into_news(source, time, title, href)
            # 获取下一页的地址
            pages = soup.find("div", {"id": "_function_code_page"}).find_all("a")
            new_url = url
            for page in pages:
                for s in page.strings:
                    if s == u"下一页":
                        new_url = base_url + page.get("href")
            if url == new_url:
                return
            else:
                url = new_url
        except Exception, e:
            print('第' + str(i) + '页出错')
            print(str(e))
            ti.sleep(40)


start()
print("完毕")
