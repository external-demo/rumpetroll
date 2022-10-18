# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: Joe Lei <joelei@tencent.com>
import json
import logging
import time

import requests

from auth.enterprise import constants
from settings import rd

LOG = logging.getLogger(__name__)
# Use connection pool
rpool = requests.Session()


def _get_method(url, params):
    """GET方法封装"""
    try:
        st = time.time()
        resp = rpool.get(url, params=params, timeout=5, verify=False)
        LOG.debug('curl -X GET "%s"', resp.url)
        result = resp.json()
        LOG.debug('RESP: %.2fms %s', (time.time() - st) * 1000, resp.text)
        return result
    except Exception:
        LOG.exception('get url {}, {} error'.format(url, params))
        return {}


def get_access_token():
    """获取调用接口凭证，有频率限制，最好有缓存"""
    params = {'corpid': constants.WECHAT_APPID, 'corpsecret': constants.WECHAT_APPSECRET}
    result = _get_method(constants.WECHAT_ACCESS_TOKEN_URL, params)
    # 错误日志
    if result.get('errcode'):
        LOG.error('get_access_token error: %s' % result)
    token = result.get('access_token', '')
    return token


def get_userid(code, access_token=None):
    """获取企业号userid
    对应是否需要访问代理, 最后做统一处理
    """
    if not access_token:
        access_token = get_access_token()
    params = {'access_token': access_token, 'code': code}
    result = _get_method(constants.WECHAT_USERID_URL, params)
    if result.get('errcode'):
        LOG.error(u"获取用户userid错误: %s" % result)
    user_id = result.get('UserId', '')
    return {'user_id': user_id, 'access_token': access_token}


def get_userinfo(user_id, access_token=None):
    """获取用户RTX信息"""
    if not access_token:
        access_token = get_access_token()
    params = {'access_token': access_token, 'userid': user_id}
    result = _get_method(constants.WECHAT_USERINFO_URL, params)
    if result.get('errcode') != 0:
        LOG.error(u"获取用户RTX信息失败: %s" % result)
    else:
        rd.hset('WEIXIN_OPEN_INFO', result['name'], json.dumps(result))
    return (result.get('name', 'Guest'), result.get('gender', '1'))
