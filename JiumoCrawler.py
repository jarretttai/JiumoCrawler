import random
import sys
import time
import re
import pymysql
from queue import Queue
import threading
import requests


# global variable
FilePath = "./keywords_zh_cn/四十万汉语大词库.txt"
StartLine = 1  # 起始行， 用于断掉后的重启
ProxyAPI = "http://127.0.0.1:5010/get_a_proxy/30?u=user2&p=pass2"
Username = ""
Password = ''
MAX_THREADS_NUM = 6
QUEUE = Queue()


def crawler(query):
    try:
        proxy = requests.get(ProxyAPI).json()
        print('    ' + str(proxy))
    except:
        time.sleep(2)
        return -1
    # 伪造初始请求， init_hubs.php，获取随机id
    now = str(int(time.time() * 1000))
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " 
                      "AppleWebKit/537.36 (KHTML, like Gecko) " 
                      "Chrome/83.0.4103.116 Safari/537.36"
    }
    payload = {
        'q': query,
        'remote_ip': '',
        'time_int': now
    }
    try:
        init_r = requests.post("https://www.jiumodiary.com/init_hubs.php", data=payload, headers=headers, proxies=proxy, timeout=8)
        if init_r.json()['status'] == "exceed":
            print("\033[0;31;43m%s\033[0m" % str(init_r.json()))
            return -1
        else:
            print("\033[0;37;42m%s\033[0m" % str(init_r.json()))
    except:
        return -1

    id = init_r.json()['id']
    # print(init_r.json())  # response of init_hubs.php
    # 伪造查询请求，ajax_fetch_hubs.php，获取文档信息
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " 
                      "AppleWebKit/537.36 (KHTML, like Gecko) " 
                      "Chrome/83.0.4103.116 Safari/537.36"
    }
    payload = {
        'id': id,
        'set': 0
    }
    try:
        hub_r = requests.post("https://www.jiumodiary.com/ajax_fetch_hubs.php", data=payload, headers=headers, proxies=proxy, timeout=13)
    except:
        return -1
    return hub_r.json()


def identify_type(title):
    if re.match(r".*\.pdf", title):
        return "pdf"
    elif re.match(r".*\.docx", title):
        return "docx"
    elif re.match(r".*\.doc", title):
        return "doc"
    elif re.match(r".*\.txt", title):
        return "txt"
    elif re.match(r".*\.mobi", title):
        return "mobi"
    elif re.match(r".*\.zip", title):
        return "zip"
    elif re.match(r".*\.rar", title):
        return "rar"
    return "other"


# 格式化doc，保证格式符合数据库表的设计
def format_doc(doc):
    doc['type'] = identify_type(doc['title'])
    doc['size'] = ''
    doc['date'] = ''
    if re.match(r'文件大小: .*B', doc['des']):
        size = re.match('文件大小: .*B', doc['des']).string[6:]
        doc['size'] = size
    if doc['des'].find('分享时间: ') != -1:
        index = doc['des'].find('分享时间: ')
        date = doc['des'][(index + 6):(index + 16)]
        doc['date'] = date
    if doc['host'].find('<') != -1:
        doc['host'] = doc['host'][0:(doc['host'].find('<') - 1)]
    if len(doc['des']) > 400:
        doc['des'] = doc['des'][0:400]
    if len(doc['title']) > 200:
        doc['title'] = doc['title'][0:200]
    if len(doc['link']) >= 400:
        doc['link'] = doc['link'][0:400]
    if len(doc['size']) >= 20:
        doc['size'] = doc['size'][0:20]
    return doc


def iterate_result(result):
    res_count = 0
    doc_list = []
    for docs in result['sources']:
        if docs['view_type'] == "view_normal":
            for doc in docs['details']['data']:
                res_count += 1
                doc = format_doc(doc)
                doc_list.append(doc)
    return doc_list, res_count


def save_from_queue():
    while True:
        if QUEUE.empty():
            time.sleep(1)
            continue
        doc_list = QUEUE.get()
        print("get from queue!!")
        DB = pymysql.connect(host="localhost", user=Username, passwd=Password, db="book_worm", port=3306)
        for doc in doc_list:
            cursor = DB.cursor()
            sql = "insert into books (title, description, host, link, type, size, date, rate_summary) \
                    values ('%s', '%s', '%s', '%s', '%s', '%s','%s',%s)" % \
                    (doc['title'].replace("'", "\\'"), doc['des'].replace("'", "\\'"),
                    doc['host'], doc['link'], doc['type'], doc['size'], doc['date'], doc['rate_summary'])
            cursor.execute(sql)
            DB.commit()
            cursor.close()
        DB.close()
        print("save to mysql!!!")
        

def search_and_save(query, line_num, semaphor):
    semaphor.acquire()
    for i in range(21):
        print("Line " + str(line_num) + " of keyword \"" + query + "\" starting...")
        result = crawler(query)
        if result != -1:
            break
    if i == 20:
        sys.exit(1)
    doc_list, res_count = iterate_result(result)
    QUEUE.put(doc_list)
    print("\033[1;37;44m[" + str(res_count) + " RESULTS] "+"Line " + str(line_num) + " of keyword \"" + query + "\" finished!\033[0m")
    time.sleep(1)
    semaphor.release()
    

def main():
    line_num = 0  # 统计行数
    f = open(FilePath, encoding='utf-8')
    line = f.readline()
    semaphore = threading.BoundedSemaphore(MAX_THREADS_NUM)
    save_to_db = threading.Thread(target=save_from_queue)
    save_to_db.start()
    while line:
        line_num += 1
        if line_num < StartLine:
            line = f.readline()
            continue
        query = re.split(r'\W+', line)[0]
        t = threading.Thread(target=search_and_save, name=str(line_num), args=(query, line_num, semaphore))
        t.start()
        line = f.readline()


if __name__ == "__main__":
    main()
