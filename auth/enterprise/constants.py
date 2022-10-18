# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: Joe Lei <joelei@tencent.com>
"""企业号常量设置"""

WECHAT_APPID = 'wxab249edd27d57738'
# 蓝鲸助手ECRET
WECHAT_APPSECRET = 'pYamqZulCzwTqTqJ-CAquLrCy9d4PWVPYeXIEWzFcYc9R_DDQ7XNwli7NOGDXg5h'

# 获取ACCESS_TOKEN，
# 每企业调用单个cgi/api不可超过1000次/分，30000次/小时，
# 每ip调用单个cgi/api不可超过2000次/分，60000次/小时
WECHAT_ACCESS_TOKEN_URL = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
# 跳转链接
WECHAT_OAUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
# 通过跳转URL的CODE获取user_id
WECHAT_USERID_URL = 'https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo'
# 通过user_id获取RTX信息
WECHAT_USERINFO_URL = 'https://qyapi.weixin.qq.com/cgi-bin/user/get'
