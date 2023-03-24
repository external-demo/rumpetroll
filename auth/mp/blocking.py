"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import json
import logging
import os

import requests

from common.signer import signed_urlopen
from settings import RD

HNAME = 'WEIXIN_OPEN_INFO'
LOG = logging.getLogger(__name__)


def get_name(openid):
    """获取名称"""
    url = '/lottery/get_user_info/'
    try:
        params = {'api_secret_key': '2RQ9tdsaf12jdfjkjldoisjFEjofj', 'openid': openid}
        resp = requests.get(url, params=params, timeout=3).json()
        name = resp['data'].get('name')
        return True if name else False
    except Exception:
        LOG.exception('get_name error')
        return False


def get_nickname(openid):
    """获取微信昵称"""
    url = '/api/get_weixin_info/'
    try:
        os.environ['APP_CODE'] = 'got_open'
        os.environ['SECRET_KEY'] = 'sdsdfsdfslkdfjlsdjflksdahjflks'
        url = '{}?openid={}'.format(url, openid)
        resp = signed_urlopen(url, timeout=5).read()
        resp = json.loads(resp)
        RD.hset(HNAME, openid, json.dumps(resp['data']))
        nickname, sex = resp['data']['nickname'], resp['data']['sex']
        return (nickname, sex)
    except Exception:
        LOG.exception('get_nickname error')
        return ('Guest', 0)
