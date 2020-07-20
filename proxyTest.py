import requests
import time
import threading


def search(keyword):
    proxy = requests.get("http://127.0.0.1:5010/get_a_proxy/30?u=user2&p=pass2").json()
    print(proxy)
    now = str(int(time.time() * 1000))
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.8,en;q=0.7,zh-TW;q=0.4",
        "content-type": "application/x-www-form-urlencoded",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                    "AppleWebKit/537.36 (KHTML, like Gecko) " \
                    "Chrome/83.0.4103.116 Safari/537.36"
    }
    payload = {
        'q': KeyWord,
        'remote_ip': '',
        'time_int': now
    }

    init_r = requests.post("https://www.jiumodiary.com/init_hubs.php", data=payload, headers=headers,
                        proxies=proxy)
    print(init_r.json())  # response of init_hubs.php


if __name__ == "__main__":
    for i in range(10):
        KeyWord = 'mao'
        print(i)
        t = threading.Thread(target=search, args=(KeyWord,))
        t.start()


