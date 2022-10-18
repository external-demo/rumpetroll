# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: Joe Lei <joelei@tencent.com>
"""重试模块
"""
import logging
from functools import wraps

LOG = logging.getLogger(__name__)


class Retrying(Exception):
    pass


def retry(func):
    @wraps(func)
    def _wrapped_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Retrying:
            kwargs['use_cache'] = False
            LOG.warning('Retrying %s, %s, %s', func, args, kwargs)
            return func(*args, **kwargs)

    return _wrapped_func
