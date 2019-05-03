# encoding=utf-8

from __future__ import print_function
from bs4 import BeautifulSoup
from urllib import request
from sqlutil import sqlutil
import requests
import time as ti

'''
Created on 2016年7月17日
中国新闻网关于自贸区的内容
@author: Cesar
'''

headers = {'User-Agent': "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11"}
base_url = "http://sou.chinanews.com/search.do?q=%E8%87%AA%E8%B4%B8%E5%8C%BA"

start_page = 1
max_page = 8


# 1. 存储新闻的链接和时间
def get_all_link():
    for i in range(start_page, max_page):
        try:
            print('第' + str(i) + '页：')
            # 获取页面源码
            data = {"q": "自贸区", "ps": 10, "start": i * 10 - 10, "type": "", "sort": "pubtime", "time_scope": "0",
                    "channel": "all",
                    "adv": 1, "day1": "", "day2": "", "field": "", "creator": ""}
            html = requests.post(base_url, headers=headers, data=data).text
            soup = BeautifulSoup(html, "html.parser")
            time_sources = soup.find_all("li", {"class": "news_other"})
            for time_source in time_sources:
                link = time_source.string.split("\n")[0].strip()
                time = time_source.string.split("\n")[1].strip()
                # print(time)
                sqlutil.insert_into_news("中国新闻网", time, "", link)
            ti.sleep(1)
        except Exception as e:
            print('第' + str(i) + '页出错')
            print(str(e))
            ti.sleep(20)


def get_content_of_link(url):
    request1 = request.Request(url)
    response = request.urlopen(request1)  # 取得响应
    html = response.read()  # 获取网页内容
    html = html.decode('gbk', 'ignore')  # 将gbk编码转为unicode编码
    html = html.encode('utf-8', 'ignore')  # 将unicode编码转为utf-8编码
    soup = BeautifulSoup(html, "html.parser")
    # 去掉script标签
    [s.extract() for s in soup("script")]
    # 获得标题
    title = soup.title.string.replace(u"-中新网", "")
    # 获得来源,没有为空
    source = ""
    try:
        time_source = soup.find("div", {"class": "left-time"}).find("div", {"class": "left-t"}).strings
        for s in time_source:
            time_source = s
            break
        source = time_source.split(u"来源：")[1].strip()
    except Exception as e:
        print(str(e))
        ti.sleep(2)
    # 获得正文，没有为所有字
    content = ""
    try:
        content = "\n".join([s.strip().replace("\n", "") for s in soup.find("div", {"class": "left_zw"}).strings])
    except Exception as e:
        print(str(e))
        ti.sleep(2)
    return title, source, content


# 2. 获取并解析新闻具体内容
def get_all_content():
    sina_news_ids, sources, titles, contents, times, urls = sqlutil.get_all_link_without_content()
    print("共" + str(len(contents)) + "条数据")
    for i in range(len(urls)):
        ti.sleep(1)
        try:
            if urls[i] == "":
                continue
            title, source, content = get_content_of_link(urls[i])
            if title is not None and title != u"":
                title = title.replace(u"--中新网", u"")
            if source == u"" or content is None:
                source = sources[i]
            if content == u"" or content is None:
                content = contents[i]
            else:
                content.replace(u"中新网", u"")
            sqlutil.update_news(sina_news_ids[i], source, title, content)
            print(u"第" + str(i) + u"条数据完成")
        except Exception as e:
            print(str(e))
            print("第" + str(i) + "条数据出错")
            print(urls[i])
            sqlutil.delete_news_by_id(sina_news_ids[i])


if __name__ == '__main__':
    get_all_link()
    get_all_content()


def start():
    get_all_link()
    get_all_content()
