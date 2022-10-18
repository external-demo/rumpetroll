# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: 蓝鲸智云
import json
import logging

from tornado import gen

from auth.mp import constants
from common.retrying import Retrying
from common.signer import get_signed_url
from common.utils import http_get
from settings import rd, region

LOG = logging.getLogger(__name__)


@gen.coroutine
def get_access_token(use_cache=True):
    """获取调用接口凭证，有频率限制，最好有缓存"""
    if use_cache:
        access_token = region.get('access_token')
        LOG.debug('get_access_token use cache: %s' % access_token)
    else:
        access_token = None

    if not access_token:
        url = get_signed_url(
            constants.WECHAT_ACCESS_TOKEN_URL, app_code=constants.APP_CODE, secret_key=constants.SECRET_KEY
        )
        result = yield http_get(url)
        # 错误日志
        if not result.get('result'):
            LOG.error('get_access_token error: %s' % result)
            access_token = None
        else:
            access_token = result['data'].get('access_token')
            region.set('access_token', access_token)
    raise gen.Return(access_token)


@gen.coroutine
def get_userinfo(user_id, access_token=None, use_cache=True):
    """获取用户RTX信息"""
    if not access_token:
        access_token = yield get_access_token(use_cache=use_cache)
        if not access_token and use_cache is True:
            raise Retrying
    params = {'access_token': access_token, 'openid': user_id, 'lang': 'zh_CN'}

    cache_key = 'get_userinfo::%s' % user_id

    if use_cache:
        result = region.get(cache_key)
        LOG.debug('get_userinfo[%s] use cache: %s', user_id, result)
    else:
        result = None

    if not result:
        result = yield http_get(constants.WECHAT_USERINFO_URL, params)
        if result.get('errcode'):
            LOG.error(u"获取用户微信信息失败: %s" % result)
            if use_cache is True:
                raise Retrying
        else:
            region.set(cache_key, result)
            rd.hset('WEIXIN_OPEN_INFO', result['openid'], json.dumps(result))

    raise gen.Return((result.get('nickname', 'Guest'), result.get('sex', '1')))
