# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: 蓝鲸智云
"""
公众号常量
"""
import os

WECHAT_APPID = os.environ.get("WECHAT_APPID")
WECHAT_APPSECRET = os.environ.get("WECHAT_APPSECRET")

WECHAT_OAUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'

# 或者微信昵称
WECHAT_USERINFO_URL = 'https://api.weixin.qq.com/cgi-bin/user/info'

WECHAT_ACCESS_TOKEN_URL = os.environ.get("WECHAT_ACCESS_TOKEN_URL")

# WECHAT_USERINFO_URL
WECHAT_USERID_URL = os.environ.get("WECHAT_ACCESS_TOKEN_URL")

# 蓝鲸接口鉴权
APP_CODE = os.environ.get("TENCENT_APP_CODE")
SECRET_KEY = os.environ.get("TENCENT_SECRET_KEY")
QQ_UIN = os.environ.get("QQ_UIN")
