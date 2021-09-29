import json
import uuid
import time
import hashlib
import requests

from .debug import Debug


def query_translation(settings, text):
    def truncate(q):
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

    def encrypt(signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()

    api_url = settings.get('api_url', '')
    app_key = settings.get('app_key', '')
    secret = settings.get('app_secret', '')
    if (api_url and app_key and secret):
        curtime = str(int(time.time()))
        salt = str(uuid.uuid1())
        sign = encrypt(app_key + truncate(text) + salt + curtime + secret)
        data = {
            'q': text,
            'from': settings.get('from', 'auto'),
            'to': settings.get('to', 'auto'),
            'appKey': app_key,
            'salt': salt,
            'sign': sign,
            'signType': 'v3',
            'curtime': curtime
        }

    else:
        data = { 'q': text }
        api_url = 'http://fanyi.youdao.com/openapi.do?keyfrom=divinites&key=1583185521&type=data&doctype=json&version=1.1'

    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        Debug.print('begin request')
        Debug.pprint(data)
        Debug.done_msg = 'Failed!'
        response = requests.post(
            api_url, data=data, headers=headers, timeout=5.0)
        json_data = json.loads(response.content.decode('utf-8'))
        Debug.done_msg = 'Succeed.'
        Debug.print('succeed request')
        Debug.pprint(json_data)
    except requests.exceptions.ConnectionError:
        Debug.error(u'连接失败，请检查你的网络状态')
    except requests.exceptions.Timeout:
        Debug.error(u'连接超时，请检查你的网络状况')
    except requests.exceptions.InvalidURL:
        Debug.error(u'无效的URL，请检查你的"api_url"设置')
    except requests.exceptions.HTTPError:
        Debug.error(u'HTTP请求错误')
    except Exception as e:
        Debug.print(e)
        Debug.error(u'很抱歉，由于未知原因，暂时无法为您翻译')
    else:
        return json_data
    raise
