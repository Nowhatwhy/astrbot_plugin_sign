import random
import time
import requests
import hashlib
from datetime import datetime

taskId = '333c5a2a7b291cb02d333fcf18f60843'
DEFAULT_PASSWD = "Ahgydx@920"


# 用户认证函数
def get_flysource_auth(user_id, user_password):
    user_password_hash = hashlib.md5(user_password.encode()).hexdigest()
    url = f'https://xskq.ahut.edu.cn/api/flySource-auth/oauth/token?tenantId=000000&username={user_id}&password={user_password_hash}&type=account&grant_type=password&scope=all'
    data = {
        'tenantId': '000000',
        'username': user_id,
        'password': user_password_hash,
        'type': 'account',
        'grant_type': 'password',
        'scope': 'all'
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": 'Basic Zmx5c291cmNlX3dpc2VfYXBwOkRBNzg4YXNkVURqbmFzZF9mbHlzb3VyY2VfZHNkYWREQUlVaXV3cWU=',
        "Content-Length": "0",
        "Host": "xskq.ahut.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    resp = requests.post(url, data, headers=headers).json()
    return resp['access_token']


# 签到函数
def qd(user_id, user_password=DEFAULT_PASSWD):
    try:
        flysource_auth = get_flysource_auth(user_id, user_password)
    except Exception as e:
        print(f"用户 {user_id} 登录失败: {e}")
        return '登录遇到问题'

    time.sleep(random.random())

    url = 'https://xskq.ahut.edu.cn/api/flySource-yxgl/dormSignRecord/add'
    headers = {
        'content-type': 'application/json;charset=UTF-8',
        'authorization': "Basic Zmx5c291cmNlX3dpc2VfYXBwOkRBNzg4YXNkVURqbmFzZF9mbHlzb3VyY2VfZHNkYWREQUlVaXV3cWU=",
        'FlySource-sign': "58ae933c48b5770fdb84b293918ffa751.MTc1NjY1MDYzMzYyMw==",
        'flysource-auth': f'bearer {flysource_auth}',
        'host': 'xskq.ahut.edu.cn',
        'referer': f'https://xskq.ahut.edu.cn/wise/pages/ssgl/dormsign?taskId={taskId}&autoSign=1&scanSign=0&userId={user_id}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }

    data = {
        'locationAccuracy': 0.4,
        'signDate': datetime.now().strftime('%Y-%m-%d'),
        'signLat': 31.675667,
        'signLng': 118.556382,
        'signTime': datetime.now().strftime('%H:%M:%S'),
        'signType': 0,
        'signWeek': ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'][datetime.now().weekday()],
        'taskId': taskId
    }

    # 模拟请求 1
    resp_1 = requests.get(
        'https://xskq.ahut.edu.cn/api/flySource-base/wechat/getWechatMpConfig?configUrl=https%253A%252F%252Fxskq.ahut.edu.cn%252Fwise%252Fpages%252Flogin%252Fwechat_mp%253Fcode%253D021kmrll22rYdg46kOkl2MkWBr3kmrlI%2526state%253D0c5aeacee1b3ca1489fbc9c22a1c71f0',
        headers=headers).json()

    # 重新定义 headers（和上面差不多，只是 sign 不一样）
    headers['FlySource-sign'] = '31cb00b97096957e2e49156f863f96391.MTczNTU3MDU5MjQxMQ=='

    # 签到请求
    resp_2 = requests.post(url, headers=headers, json=data).json()

    print(f"用户 {user_id} 签到结果:")
    print("请求1:", resp_1)
    print("请求2:", resp_2)

    return f"url_1:{resp_1.get('msg', '')}\nurl_2:{resp_2.get('msg', '')}\n"


# 执行所有用户的签到操作
def run_sign_in():
    users = [
            "239074022",   #默认密码的，直接填学号
        ]

    results = []
    for u in users:
        if isinstance(u, str):
            user_id, passwd = u, DEFAULT_PASSWD
        else:
            user_id, passwd = u[0], u[1]

        result = qd(user_id, passwd)
        results.append(f"用户 {user_id}: \n{result}\n")
    return results


if __name__ == "__main__":
    print("脚本启动，立即执行签到")
    run_sign_in()