# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
import tornado

import settings
from handlers import api, main, ws

handlers = [
    (r"/", main.IndexHandler),
    (r"/rumpetroll", main.IndexHandler),
    (r"/rumpetroll/", main.IndexHandler),
    (r"/rumpetroll/login/", main.LoginHandler),
    (r"/rumpetroll/admin/", main.AdminHandler),
    (r"/rumpetroll/rank/", main.RankHandler),
    (r"/rumpetroll/error/", main.ErrorHandler),
    # 多节点 统一socket.io前缀
    (r"/rumpetroll/socket.io/(?P<server>[a-z-_A-Z0-9]+)/(?P<port>[a-z-_A-Z0-9]+)/", ws.WSHandler),
    # 单节点
    (r"/rumpetroll/socket.io/(?P<port>[a-z-_A-Z0-9]+)/", ws.WSHandler),
    # 开发环境
    (r"/rumpetroll/socket.io/", ws.WSHandler),
    (r"/rumpetroll/api/get_endpoint/", api.GetEndpointHandler),
    (r"/rumpetroll/api/get_username/", api.GetUserNameHandler),
    (r"/rumpetroll/api/stat/", api.GetStatHandler),
    (r"/rumpetroll/api/user/", api.GetUserHandler),
    (r"/rumpetroll/api/gold/", api.GoldsHandler),
    (r"/rumpetroll/api/export/", api.ExportHandler),
    (r"/rumpetroll/api/func_controller/", api.FunctionController),
    (r"/rumpetroll/api/clean/", api.CleanHandler),
    # for debug static, product use nginx
    (r'/rumpetroll/static/(.*)', tornado.web.StaticFileHandler, {'path': settings.settings['static_path']}),
]
