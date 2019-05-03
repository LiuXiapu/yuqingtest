# -*-coding:utf-8 -*-

"""
知乎的爬虫，没有加入到主线程，原因是数量不多，
打开定期爬一次即可。
注：使用之前需要将数据库切换到
zimaoqu
"""


import requests
from bs4 import BeautifulSoup
from sqlutil import sqlutil
import time

QUESTION_URL = 'http://www.zhihu.com/question/{id}'
QUESTION_COMMENTS_URL = 'http://www.zhihu.com/node/QuestionCommentBoxV2?params=%7B"question_id":{id}%7D'
ANSWER_COMMENTS_URL = 'http://www.zhihu.com/node/AnswerCommentBoxV2?params=%7B%22answer_id%22%3A%22{id}%22%2C%22load' \
                      '_all%22%3Atrue%7D'

headers = {'User-Agent': "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11"}


# DB_CONFIG = {'host': '127.0.0.1', 'unix_socket': '/tmp/mysql.sock', 'user': 'root', 'passwd': None, 'charset': 'utf8',
#              'db': 'FreeTradeZone'}


def get_links_by_page(topic, page):
    html = requests.get('http://www.zhihu.com/topic/%s/questions?page=%s' % (topic, str(page)), headers=headers).text
    soup = BeautifulSoup(html)
    question_feeds = soup.find('div', {'id': 'zh-topic-questions-list'}).find_all('div', {'class': 'feed-item'})
    question_link_list = list()
    for feed in question_feeds:
        a = feed.find('a', {'class': 'question_link'})
        link = 'http://www.zhihu.com' + a['href']
        title = a.get_text()
        result = {'link': link, 'title': title}
        question_link_list.append(result)
    return question_link_list


def get_all_links(topic):
    html = requests.get('https://www.zhihu.com/topic/%s/questions?page=1' % topic, headers=headers).text
    soup = BeautifulSoup(html)
    pages = int(soup.find('div', {'class': 'zm-invite-pager'}).find_all('span')[-2].get_text())
    result = list()
    for i in range(1, pages + 1):
        print('正在抓取第%d页的link,共%d页' % (i, pages))
        result += get_links_by_page(topic, i)
    return result


# links=get_all_links('19866310')
# for link in links:
# 	print(link['link']+'\t'+link['title'])

# 25512567
def scrawl_question(url):
    # conn = pymysql.connect(host=DB_CONFIG["host"], unix_socket=DB_CONFIG["unix_socket"], user=DB_CONFIG["user"],
    #                        passwd=DB_CONFIG["passwd"], charset=DB_CONFIG["charset"], db=DB_CONFIG["db"])

    # html=requests.get(QUESTION_URL.format(id='25512567')).text
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html)
    question_id = soup.find('div', {'id': 'zh-question-detail'})['data-resourceid']
    question_title = soup.find('div', {'id': 'zh-question-title'}).get_text().strip()
    if soup.find('div', {'id': 'zh-question-detail'}).find('div', {'class': 'zm-editable-content'}):
        question_content = soup.find('div', {'id': 'zh-question-detail'}).find('div', {
            'class': 'zm-editable-content'}).get_text()
    else:
        question_content = BeautifulSoup(
            soup.find('div', {'id': 'zh-question-detail'}).find('textarea').get_text()).get_text()
        print(question_content)

    sqlutil.insert_zh_question(question_id, question_title, question_content)
    # cur = conn.cursor()
    # cur.execute('insert ignore into zh_questions (id,title,content) values(%s,%s,%s)',
    #             (question_id, question_title, question_content))  # SQL
    # cur.close()
    # conn.commit()

    # 获取问题评论Ajax
    has_comments = not (
        soup.find('div', {'id': 'zh-question-meta-wrap'}).find('a',
                                                               {'name': 'addcomment'}).get_text().strip() == '添加评论')
    comments = list()
    if has_comments:
        question_comment_html = requests.get(QUESTION_COMMENTS_URL.format(id=question_id), headers=headers).text
        question_comment_soup = BeautifulSoup(question_comment_html)
        comments_divs = question_comment_soup.find('div', {'class': 'zm-comment-list'}).find_all('div', {
            'class': 'zm-item-comment'})

        for comment in comments_divs:
            comment_id = comment['data-id']
            comment_content = comment.find('div', {'class': 'zm-comment-content'}).get_text().strip()
            comment_create_time = comment.find('div', {'class': 'zm-comment-ft'}).find('span',
                                                                                       {'class': 'date'}).get_text()
            comments.append({'comment_id': comment_id, 'content': comment_content, 'create_time': comment_create_time})
            sqlutil.insert_zh_question_comment(comment_id, comment_content, comment_create_time)
            # cur = conn.cursor()
            # cur.execute('insert ignore into zh_question_comments (id,content,create_time) values(%s,%s,%s)',
            #             (comment_id, comment_content, comment_create_time))  # SQL
            # cur.close()
            # conn.commit()

    # 获取回答
    answers_divs = soup.find('div', {'id': 'zh-question-answer-wrap'}).find_all('div', {'class': 'zm-item-answer'})
    answers = list()
    for answer in answers_divs:
        answer_id = answer['data-aid']  # 回答id
        answer_content = answer.find('div', {'class': 'zm-editable-content'}).get_text().strip()  # 回答内容
        answer_time_tag = answer.find('a', {'class': 'answer-date-link'})
        if answer_time_tag.has_attr('data-tip'):
            answer_create_time = answer_time_tag['data-tip'][-10:]
        else:
            answer_create_time = answer_time_tag.get_text()[-10:]
        count_text = answer.find('a', {'name': 'addcomment'}).get_text().strip()
        answer_like = answer.find('div', {'class': 'zm-votebar'}).find('span', {'class': 'count'}).get_text()  # 回答点赞数
        answer_comments_count = 0 if count_text == u"添加评论" else int(count_text.strip(u"条评论"))  # 回答评论数
        # cur = conn.cursor()
        # cur.execute(
        #     'insert ignore into zh_answers (id,content,likes,count,create_time,question_id) \
        #       values(%s,%s,%s,%s,%s,%s)',
        #     (answer_id, answer_content, answer_like, answer_comments_count, answer_create_time, question_id))  # SQL
        # cur.close()
        # conn.commit()
        sqlutil.insert_zh_answer(answer_id, answer_content, answer_like, answer_comments_count, answer_create_time,
                                 question_id)
        answer_comments = list()
        if answer_comments_count > 0:
            # 获取回答评论Ajax
            answer_comments_html = requests.get(ANSWER_COMMENTS_URL.format(id=answer_id), headers=headers).text
            # 知乎频率限制的妥协策略
            if answer_comments_html.find(u"服务器提了一个问题"):
                for i in range(5):
                    time.sleep(30)
                    answer_comments_html = requests.get(ANSWER_COMMENTS_URL.format(id=answer_id), headers=headers).text
                    if not answer_comments_html.find(u"服务器提了一个问题"):
                        break
            answer_comments_soup = BeautifulSoup(answer_comments_html)
            # print(answer_comments_soup)
            answer_comments_divs = answer_comments_soup.find_all('div', {'class': 'zm-item-comment'})
            for comment in answer_comments_divs:
                answer_comment_id = comment['data-id']
                answer_comment_content = comment.find('div', {'class': 'zm-comment-content'}).get_text()
                answer_comment_time = comment.find('span', {'class': 'date'}).get_text()
                answer_comments.append({'content': answer_comment_content, 'create_time': answer_comment_time})
                sqlutil.insert_zh_answer_comments(answer_comment_id, answer_comment_content,
                                                  answer_comment_time, answer_id)
                # cur = conn.cursor()
                # cur.execute(
                #     'insert ignore into zh_answer_comments (id,content,create_time,answer_id) values(%s,%s,%s,%s)',
                #     (answer_comment_id, answer_comment_content, answer_comment_time, answer_id))  # SQL
                # cur.close()
                # conn.commit()
        answers.append(
            {'answer_id': answer_id, 'content': answer_content, 'comments': answer_comments, 'like': answer_like,
             'count': answer_comments_count, 'create_time': answer_create_time})
        # question = {'question_id': question_id, 'title': question_title, 'content': question_content,
        # 'comments': comments,'answers': answers}
        # conn.close()


# 19866310	自贸区topic_id
def scrawl(topic_id):
    # conn = pymysql.connect(host=DB_CONFIG["host"], unix_socket=DB_CONFIG["unix_socket"], user=DB_CONFIG["user"],
    #                        passwd=DB_CONFIG["passwd"], charset=DB_CONFIG["charset"], db=DB_CONFIG["db"])
    # cur = conn.cursor()
    # cur.execute(
    #     'truncate table zh_questions;truncate table zh_question_comments;\
    # truncate table zh_answers;truncate table zh_answer_comments;')
    # cur.close()
    # conn.commit()
    # conn.close()
    sqlutil.truncate_zh_table()
    links = get_all_links(topic_id)
    for i, link in enumerate(links):
        print('正在抓取第%d条问题\t%s' % (i, link['link']))
        try:
            scrawl_question(link['link'])
        except Exception:
            print('第%d条问题\t%s 出错' % (i, link['link']))


# scrawl_question('http://www.zhihu.com/question/36764257')
scrawl('19866310')

# print('问题标题:\t'+question['title'])
# print('问题内容:\t'+question['content'])
# print(100*'-')
# for comment in question['comments']:
# 	print(comment['content'])
# 	print(comment['create_time'])
# print(100*'-')
# for answer in question['answers']:
# 	print(answer['answer_id'])
# 	print('评论数:\t%d'%answer['count'])
# 	print('点赞数:\t'+answer['like'])
# 	print('评论内容:\t'+answer['content'])
# 	print('创建时间:\t'+answer['create_time'])
# 	for comment in answer['comments']:
# 		print(comment['content'])
# 		print(comment['create_time'])
# 	print('\n')
# 	print(100*'*')
# 	print('\n')
