# -*- coding: utf-8 -*-
# Copyright 2016 IFOOTH
# Author: 蓝鲸智云 <thezero12@hotmail.com>
import base64
import hashlib
import hmac
import logging
import os
import random
import socket
import time
from functools import wraps
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

LOG = logging.getLogger(__name__)


def signer(_func):
    """urlopen签名装饰器"""

    @wraps(_func)
    def _wrapped_view(url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, **kwargs):
        # 环境变量获取app_code, secret_key
        app_code = os.environ.get('APP_CODE', '')
        secret_key = os.environ.get('SECRET_KEY', '')

        # 生成签名参数
        _request = urlparse(url)
        query = dict(urlparse.parse_qsl(_request.query))
        query['Nonce'] = random.randint(100000, 999999)
        query['Timestamp'] = int(time.time())
        query['app_code'] = app_code
        if not data:
            method = 'GET'
            _query = '&'.join('{}={}'.format(key, value) for key, value in sorted(query.items()))
        else:
            method = 'POST'
            query['Data'] = data
            _query = '&'.join('{}={}'.format(key, value) for key, value in sorted(query.items()))
            query.pop('Data', None)

        # 签名
        raw_msg = '{}{}{}?{}'.format(method, _request.netloc, _request.path, _query)
        signature = base64.b64encode(hmac.new(secret_key, raw_msg, hashlib.sha1).digest())
        query['Signature'] = signature
        query = urlencode(query)
        # 带上签名参数
        url = '{}://{}{}?{}'.format(_request.scheme, _request.netloc, _request.path, query)
        LOG.debug('signed_urlopen req: %s' % url)
        return _func(url, data, timeout=timeout, **kwargs)

    return _wrapped_view


signed_urlopen = signer(urlopen)


def get_signed_url(url, app_code, secret_key, params, data=None):
    """获取签名URL"""
    _request = urlparse(url)
    query = dict(urlparse.parse_qsl(_request.query))
    query['Nonce'] = random.randint(100000, 999999)
    query['Timestamp'] = int(time.time())
    query['app_code'] = app_code
    query.update(params)

    if not data:
        method = 'GET'
        _query = '&'.join('{}={}'.format(key, value) for key, value in sorted(query.items()))
    else:
        method = 'POST'
        query['Data'] = data
        _query = '&'.join('{}={}'.format(key, value) for key, value in sorted(query.items()))
        query.pop('Data', None)

    # 签名
    raw_msg = '{}{}{}?{}'.format(method, _request.netloc, _request.path, _query)
    signature = base64.b64encode(hmac.new(secret_key, raw_msg, hashlib.sha1).digest())
    query['Signature'] = signature
    query = urlencode(query)
    # 带上签名参数
    url = '{}://{}{}?{}'.format(_request.scheme, _request.netloc, _request.path, query)
    LOG.debug('signed_urlopen req: %s' % url)
    return url
