# -*- coding: utf-8 -*-
import os
import math
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup


def get_file(url, max_try_time):
    if max_try_time >= 5:
        return None
    file = None
    try:
        file = urlopen(url)
    except:
        return get_file(url, max_try_time + 1)
    else:
        return file

urls = {}

url = 'https://www.dawenxue.net/2873/'
html_file = get_file(url, 0)
if html_file:
    html = BeautifulSoup(html_file.read(), 'html5lib')
    chapter_list = html.find(id = 'list').findAll('dd')
    for chapter_dd in chapter_list:
        chapter_url = chapter_dd.find('a')['href']
        chapter_name = chapter_dd.get_text()
        urls[chapter_url] = chapter_name


total_count = len(urls.keys())
count = 1
error = False

for chapter_url in urls:
    
    print(str(count) + ' / ' + str(total_count))
    count += 1
    if count < 354:
        continue
    
    html_file = get_file(url + chapter_url, 0)
    if not html_file:
        print(chapter_url + '    ' + urls[chapter_url])
    else:
        chapter_html = BeautifulSoup(html_file.read(), 'html5lib')
        chapter_text = chapter_html.find(id = 'content')
        text = str(chapter_text)[18:-6].replace('\xa0', ' ')\
            .replace('<br/>', '\n').replace('&amp;', '&')\
            .replace('&quot;', '"').replace('quot;', '"')\
            .replace('&#183;', '·')

        with open(os.getcwd() + '/chapter/' + chapter_url[:-5] + '.txt', 'w') as file:
            file.write(text + '\n')
