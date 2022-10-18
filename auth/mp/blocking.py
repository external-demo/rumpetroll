# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: 蓝鲸智云
import json
import logging
import os

import requests

from common.signer import signed_urlopen
from settings import rd

HNAME = 'WEIXIN_OPEN_INFO'
LOG = logging.getLogger(__name__)


def get_name(openid):
    """获取名称"""
    url = 'http://app.o.bkclouds.cc/got_open/lottery/get_user_info/'
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
    url = 'http://m.bkclouds.cc/bk_mobile/api/get_weixin_info/'
    try:
        os.environ['APP_CODE'] = 'got_open'
        os.environ['SECRET_KEY'] = 't)$c)oDm_P+@6u!d+QTq+(!ZQHRkt<cFUP_SKVl$Hqz.@m,She'
        url = '{}?openid={}'.format(url, openid)
        resp = signed_urlopen(url, timeout=5).read()
        resp = json.loads(resp)
        rd.hset(HNAME, openid, json.dumps(resp['data']))
        nickname, sex = resp['data']['nickname'], resp['data']['sex']
        return (nickname, sex)
    except Exception:
        LOG.exception('get_nickname error')
        return ('Guest', 0)
