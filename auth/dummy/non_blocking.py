"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
# pylint: disable=broad-except
import base64
import json
import logging

from tornado import gen

from common import constants
from settings import RD

LOG = logging.getLogger(__name__)


@gen.coroutine
def get_userid():
    """获取企业号userid
    对应是否需要访问代理, 最后做统一处理
    """
    data = {'user_id': 'Guest', 'access_token': 'Token'}
    raise gen.Return(data)


@gen.coroutine
def get_userinfo(user_id, gender=2):
    """获取用户RTX信息"""
    try:
        username = str(base64.b64decode(user_id), "utf-8") or 'Guest'
    except Exception as error:  # noqa
        LOG.error('user_id: %s not base64, %s', user_id, error)
        username = 'Guest'

    # 特殊
    if username in ['BlueKing']:
        gender = constants.FEMALE

    is_allow_login = 0
    is_online = RD.hget('rumpetroll::user_online', user_id)
    is_online = int(is_online) if is_online else 0
    if not is_online:
        is_allow_login = 1  # 允许登录
        RD.hset('rumpetroll::user_online', user_id, is_allow_login)

    data = (username, gender, is_allow_login)
    raise gen.Return(data)
