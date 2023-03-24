"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import logging

from auth.mp import constants

LOG = logging.getLogger(__name__)


def get_oauth_redirect_url(url):
    """获取oauth访问链接"""
    redirect_uri = constants.BK_MOBILE_LOGIN_URL % url
    LOG.info('redirect_url is: %s' % redirect_uri)
    return redirect_uri
