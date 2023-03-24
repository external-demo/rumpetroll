"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import logging
import urllib

from auth.mp_tencent import constants

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
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    params = urllib.urlencode(sorted_params)
    redirect_uri = '{}?{}#wechat_redirect'.format(constants.WECHAT_OAUTH_URL, params)
    LOG.info(f'redirect_url is: {redirect_uri}')
    return redirect_uri
