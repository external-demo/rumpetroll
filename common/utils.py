# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: Joe Lei <joelei@tencent.com>
import json
import logging
import time
import urllib

from tornado import gen, httpclient

import settings

if settings.HTTP_PROXY:
    httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

http_client = httpclient.AsyncHTTPClient(None, max_clients=1000)

LOG = logging.getLogger(__name__)


@gen.coroutine
def http_get(url, params={}):
    st = time.time()
    if params:
        params = urllib.urlencode(params)
        url = '{}?{}'.format(url, params)
    LOG.debug('curl -X GET "%s"', url)
    resp = yield http_client.fetch(url, method='GET', request_timeout=5, validate_cert=False, **settings.HTTP_PROXY)
    body = resp.body
    result = json.loads(body)
    LOG.debug('RESP: %.2fms %s', (time.time() - st) * 1000, body)
    raise gen.Return(result)


def object_to_json(obj):
    return json.dumps(obj.__dict__)
