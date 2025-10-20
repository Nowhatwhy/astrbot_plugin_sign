# -*- coding: utf-8 -*-
import random
import asyncio
import aiohttp
import hashlib
from . import db
from datetime import datetime
from .result import Result
taskId = '333c5a2a7b291cb02d333fcf18f60843'
DEFAULT_PASSWD = "Ahgydx@920"

# 用户认证函数（异步）
async def get_flysource_auth(user_id, user_password):
    user_password_hash = hashlib.md5(user_password.encode()).hexdigest()
    url = (
        "https://xskq.ahut.edu.cn/api/flySource-auth/oauth/token"
        f"?tenantId=000000&username={user_id}&password={user_password_hash}"
        "&type=account&grant_type=password&scope=all"
    )
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
        "Authorization": "Basic Zmx5c291cmNlX3dpc2VfYXBwOkRBNzg4YXNkVURqbmFzZF9mbHlzb3VyY2VfZHNkYWREQUlVaXV3cWU=",
        "Content-Length": "0",
        "Host": "xskq.ahut.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as resp:
            js = await resp.json()
            return js['access_token']

# 签到函数（异步）
async def qd(user_id, user_password=DEFAULT_PASSWD):
    try:
        flysource_auth = await get_flysource_auth(user_id, user_password)
    except Exception as e:
        print(f"用户 {user_id} 登录失败: {e}")
        return '登录遇到问题'

    await asyncio.sleep(random.random())

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

    async with aiohttp.ClientSession() as session:
        # 模拟请求 1（保持与原逻辑一致）
        async with session.get(
            'https://xskq.ahut.edu.cn/api/flySource-base/wechat/getWechatMpConfig?configUrl=https%253A%252F%252Fxskq.ahut.edu.cn%252Fwise%252Fpages%252Flogin%252Fwechat_mp%253Fcode%253D021kmrll22rYdg46kOkl2MkWBr3kmrlI%2526state%253D0c5aeacee1b3ca1489fbc9c22a1c71f0',
            headers=headers
        ) as _resp1:
            _ = await _resp1.json()

        # 重新定义 headers 中的 sign（保持与原逻辑一致）
        headers['FlySource-sign'] = "31cb00b97096957e2e49156f863f96391.MTczNTU3MDU5MjQxMQ=="

        # 签到请求
        async with session.post(url, headers=headers, json=data) as resp2:
            js = await resp2.json()
            return js

# 下面三个函数仅把调用 qd 的部分改成了 await，其它逻辑/返回完全不变
async def sign(user)-> Result:
    """输入用户，执行签到"""
    result = Result(False, user.id if user else -1, user.user_name if user else "", "")
    if not user:
        result.success = False
        result.mes = "用户不存在，请先创建用户"
        return result

    result.user_id = user.id
    result.user_name = user.user_name
    if user.e_coin < 5:
        result.success = False
        result.mes = "E币余额不足，至少需要5E币才能签到"
        return result

    res = await qd(user.stu_id, DEFAULT_PASSWD)

    if res == '登录遇到问题':
        result.success = False
        result.mes = "登录遇到问题，请检查学号和密码是否正确"
        return result

    if  res.get('success'):
        db.update_balance(user.id, -5)  # 扣除5 E币
        result.success = True
        result.mes = "扣除5E币作为签到费用"
        return result
    else:
        result.success = False
        result.mes = res.get('msg', '未知错误')
        return result

async def sign_single(id: int):
    """输入id，执行签到"""
    user = db.get_user(id)
    return await sign(user)

async def sign_all():
    """执行所有用户签到"""
    users = db.get_user_list()
    results = []
    for user in users:
        res = await sign(user)
        results.append(res)
    return results

if __name__ == "__main__":
    # 示例：单人签到
    print(asyncio.run(sign_single(736644851)))