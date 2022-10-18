# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: Joe Lei <joelei@tencent.com>
import logging
import urllib

from auth.enterprise import constants

LOG = logging.getLogger(__name__)


def get_oauth_redirect_url(url, state='authenticated'):
    """获取oauth访问链接"""
    params = {
        'appid': constants.WECHAT_APPID,
        'redirect_uri': url,
        'response_type': 'code',
        'scope': 'snsapi_base',
        'state': state,
    }
    params = urllib.urlencode(params)
    redirect_uri = '{}?{}#wechat_redirect'.format(constants.WECHAT_OAUTH_URL, params)
    LOG.info('redirect_url is: %s' % redirect_uri)
    return redirect_uri
