# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: 蓝鲸智云
import redis_lock

import settings


def get_lock():
    """获取一个锁对象"""
    return redis_lock.Lock(settings.rd, settings.LOCK_NAME)
