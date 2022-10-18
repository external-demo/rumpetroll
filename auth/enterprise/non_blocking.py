# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: Joe Lei <joelei@tencent.com>
import json
import logging

from tornado import gen

from auth.enterprise import constants
from common.retrying import Retrying
from common.utils import http_get
from settings import rd, region

LOG = logging.getLogger(__name__)


@gen.coroutine
def get_access_token(use_cache=True):
    """获取调用接口凭证，有频率限制，最好有缓存"""
    params = {'corpid': constants.WECHAT_APPID, 'corpsecret': constants.WECHAT_APPSECRET}
    if use_cache:
        result = region.get('access_token')
        LOG.debug('get_access_token use cache: %s' % result)
    else:
        result = None

    if not result:
        result = yield http_get(constants.WECHAT_ACCESS_TOKEN_URL, params)
        # 错误日志
        if result.get('errcode'):
            LOG.error('get_access_token error: %s' % result)
        else:
            region.set('access_token', result)
    token = result.get('access_token', '')
    raise gen.Return(token)


@gen.coroutine
def get_userid(code, access_token=None, use_cache=True):
    """获取企业号userid
    对应是否需要访问代理, 最后做统一处理
    """
    if not access_token:
        access_token = yield get_access_token(use_cache=use_cache)
        if not access_token and use_cache is True:
            raise Retrying
    params = {'access_token': access_token, 'code': code}
    result = yield http_get(constants.WECHAT_USERID_URL, params)
    if result.get('errcode'):
        LOG.error(u"获取用户userid错误: %s" % result)
        if use_cache is True:
            raise Retrying
    user_id = result.get('UserId', '')
    raise gen.Return({'user_id': user_id, 'access_token': access_token})


@gen.coroutine
def get_userinfo(user_id, access_token=None, use_cache=True):
    """获取用户RTX信息"""
    if not access_token:
        access_token = yield get_access_token(use_cache=use_cache)
        if not access_token and use_cache is True:
            raise Retrying
    params = {'access_token': access_token, 'userid': user_id}

    cache_key = 'get_userinfo::%s' % user_id

    if use_cache:
        result = region.get(cache_key)
        LOG.debug('get_userinfo[%s] use cache: %s', user_id, result)
    else:
        result = None

    if not result:
        result = yield http_get(constants.WECHAT_USERINFO_URL, params)
        if result.get('errcode') != 0:
            LOG.error(u"获取用户RTX信息失败: %s" % result)
            if use_cache is True:
                raise Retrying
        else:
            region.set(cache_key, result)
            rd.hset('WEIXIN_OPEN_INFO', result['name'], json.dumps(result))

    raise gen.Return((result.get('name', 'Guest'), result.get('gender', '1')))
