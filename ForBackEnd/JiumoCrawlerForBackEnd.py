import time
import re
import json
import requests


def crawler(query):
    # 伪造初始请求， init_hubs.php，获取随机id
    now = str(int(time.time() * 1000))
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest"
    }
    payload = {
        'q': query,
        'remote_ip': '',
        'time_int': now
    }
    init_r = requests.post("https://www.jiumodiary.com/init_hubs.php", data=payload, headers=headers)
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
        "x-requested-with": "XMLHttpRequest"
    }
    payload = {
        'id': id,
        'set': 0
    }
    hub_r = requests.post("https://www.jiumodiary.com/ajax_fetch_hubs.php", data=payload, headers=headers)
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
        size = re.match('文件大小: ', doc['des']).string[6:]
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


def main():
    query = input('keyword: ')
    # 调用功能函数
    result = crawler(query)
    doc_list, res_count = iterate_result(result)
    for doc in doc_list:
        print(json.dumps(doc, sort_keys=True, indent=2, separators=(',', ':'), ensure_ascii=False))


if __name__ == "__main__":
    main()
