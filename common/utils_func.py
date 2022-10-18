# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: Joe Lei <joelei@tencent.com>
import datetime
import json
import logging

from settings import rd as redis_client

FUNCTION_KEY = 'rumpetroll::function_control'

LOG = logging.getLogger(__name__)


def func_control(func_code):
    try:
        data = redis_client.hget(FUNCTION_KEY, func_code)
        if data:
            data = json.loads(data)
            return (data['enabled'], data['wlist'])
        else:
            # 没找到，设置为未开启，白名单为空
            return (True, [])
    except Exception:
        LOG.warning('func_control %s error', func_code)
        return (True, [])


def get_func_control(func_code):
    """活动功能开关"""
    try:
        data = redis_client.hget(FUNCTION_KEY, func_code)
        if data:
            data = json.loads(data)
            return data
        else:
            # 没找到，设置为未开启，白名单为空
            return {}
    except Exception:
        LOG.warning('get_func_control %s error', func_code)
        return {}


def set_func_control(func_code, func_name='', enabled=False, wlist=None):
    """设置功能开关"""
    if not wlist:
        wlist = []

    enabled = bool(enabled)

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {'func_code': func_code, 'func_name': func_name, 'enabled': enabled, 'wlist': wlist, 'updated_at': now}
    data = json.dumps(data)
    return redis_client.hset(FUNCTION_KEY, func_code, data)
