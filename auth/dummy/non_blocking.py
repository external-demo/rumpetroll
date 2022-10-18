# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: 蓝鲸智云
import base64
import json
import logging

from tornado import gen

from common import constants
from settings import rd

LOG = logging.getLogger(__name__)


@gen.coroutine
def get_userid(code, access_token=None, use_cache=True):
    """获取企业号userid
    对应是否需要访问代理, 最后做统一处理
    """
    data = {'user_id': 'Guest', 'access_token': 'Token'}
    raise gen.Return(data)


@gen.coroutine
def get_userinfo(user_id, access_token=None, use_cache=True, gender=2):
    """获取用户RTX信息"""
    try:
        username = base64.b64decode(user_id) or 'Guest'
    except Exception as error:
        LOG.error('user_id: %s not base64, %s', user_id, error)
        username = 'Guest'

    # 特殊
    if username in ['BlueKing']:
        gender = constants.FEMALE

    data = (username, gender)
    rd.hset('WEIXIN_OPEN_INFO', user_id, json.dumps({"nickname": username, 'gender': gender}))
    raise gen.Return(data)
