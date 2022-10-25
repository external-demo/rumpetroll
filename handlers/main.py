# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
import base64
import json
import logging
import settings
import tornado.web
from tornado import gen
from httpx import post
from auth import non_blocking as wx_client
from auth import utils as wx_utils
from handlers.utils import authenticated, get_rank, is_started

LOG = logging.getLogger(__name__)


def get_login_url(request):
    return 'http://%s/rumpetroll/login/' % request.host


def get_register_server_url():
    return "http://{host}:{port}/register".format(host=settings.USER_SERVER_HOST, port=settings.USER_SERVER_PORT)


def get_login_server_url():
    return "http://{host}:{port}/login".format(host=settings.USER_SERVER_HOST, port=settings.USER_SERVER_PORT)


def get_websocket_url(request):
    return 'ws://%s/rumpetroll/socket.io/' % request.host


class IndexHandler(tornado.web.RequestHandler):
    @gen.coroutine
    @is_started
    @tornado.web.addslash
    def get(self):
        openid = self.get_cookie('openid', '')

        token = self.get_argument('token', '')
        is_token = 0
        if token == settings.TOKEN:
            openid = self.get_argument('openid', 'is__superuser')
            openpwd = self.get_argument('openid', 'is__superuser')
            gender = self.get_argument('gender', '1')
            is_token = 1
            self.set_cookie('openid', openid)
            self.set_cookie('openpwd', openpwd)
            self.set_cookie('gender', gender)

        elif openid == '':
            url = '{}?next=http://{}{}'.format(get_login_url(self.request), self.request.host, self.request.uri)
            self.redirect(url)
            raise gen.Return()

        ctx = {
            'static_url': settings.STATIC_URL,
            'is_token': is_token,
            'version': settings.STATIC_VERSION,
            'over_time': settings.OVERTIME,
            'SETTINGS': settings,
            'WEBSOCKET_URL': get_websocket_url(self.request),
        }

        self.render('rumpetroll.html', **ctx)


class LoginHandlerWX(tornado.web.RequestHandler):
    @gen.coroutine
    @is_started
    def get(self):
        location = self.get_argument('next', '').strip()
        if not location:
            location = 'http://m.bkclouds.cc/rumpetroll/'

        # 已经验证用户先登出，再跳转
        openid = self.get_cookie('openid', '')
        if openid:
            self.clear_cookie('openid')

        code = self.get_argument('code', '')
        state = self.get_argument('state', '')

        if code and state == 'authenticated':
            result = yield wx_client.get_userid(code)
            if result['user_id']:
                openid = result['user_id']
                self.set_cookie('openid', openid)
                self.redirect(location)
                raise gen.Return()
            else:
                ctx = {'static_url': settings.STATIC_URL, 'message': u"登录已经失效，请刷新后重试！", 'SETTINGS': settings}
                self.render("wx_error.html", **ctx)
                raise gen.Return()

        elif not state:
            url = 'http://{}{}'.format(self.request.host, self.request.uri)
            self.redirect(wx_utils.get_oauth_redirect_url(url))
            raise gen.Return()

        ctx = {
            'static_url': settings.STATIC_URL,
            'message': u"登录已经失效，请刷新后重试！",
            'version': settings.STATIC_VERSION,
            'SETTINGS': settings,
        }
        self.render("wx_error.html", **ctx)
        raise gen.Return()


class RegisterHandler(tornado.web.RequestHandler):
    @gen.coroutine
    @is_started
    def get(self):
        ctx = {
            'static_url': settings.STATIC_URL,
            'message': "用户名已被使用",
            'version': settings.STATIC_VERSION,
            'SETTINGS': settings,
        }
        self.render("register.html", **ctx)

    def post(self):
        location = 'http://%s/rumpetroll/' % self.request.host
        register_location = 'http://{}/rumpetroll/register/'.format(self.request.host)

        username = self.get_argument('username')
        gender = self.get_argument('gender')
        password = self.get_argument("password")

        if username and (len(username) >= 1) and (gender in ['1', '2']) and password and (len(password) >= 3):
            register_res = self.register({
                "username": username, "password": password,
                "gender": gender
            })
            if not register_res.get("status", False):
                location = register_location
        else:
            location = register_location
        self.redirect(location)

    def register(self, data: dict) -> dict:
        try:
            rep_data = post(url=get_register_server_url(), json=data, verify=False, timeout=10)
            return rep_data.json()
        except:
            return {}


class LoginHandler(tornado.web.RequestHandler):
    @gen.coroutine
    @is_started
    def get(self):
        # 已经验证用户先登出，再跳转
        self.clear_cookie('openid')
        self.clear_cookie('gender')
        self.clear_cookie('openpwd')
        ctx = {
            'static_url': settings.STATIC_URL,
            'message': u"登录已经失效，请刷新后重试！",
            'version': settings.STATIC_VERSION,
            'SETTINGS': settings,
        }
        self.render("login.html", **ctx)

    @is_started
    def post(self):
        location = self.get_argument('next', '').strip()
        if not location:
            location = 'http://%s/rumpetroll/' % self.request.host

        username = self.get_argument('username')
        gender = self.get_argument('gender')
        password = self.get_argument("password")

        if username and (len(username) >= 1) and (gender in ['1', '2']) and password and (len(password) >= 3):
            openid = base64.b64encode(username.encode('utf-8'))
            openpwd = base64.b64encode(password.encode('utf-8'))
            self.set_cookie('openid', openid)
            self.set_cookie('openpwd', openpwd)
            self.set_cookie('gender', gender)
            login_res = self.login({
                "username": username, "password": password,
                "gender": gender
            })
            if not login_res.get("status", False):
                location = "http://%s/rumpetroll/error/?type=server_error&token=%s" % (self.request.host, settings.TOKEN)
        else:
            location = '{}?next=http://{}/rumpetroll/'.format(get_login_url(self.request), self.request.host)

        self.redirect(location)

    def login(self, data: dict) -> dict:
        try:
            req_data = post(url=get_login_server_url(), json=data, verify=False, timeout=10)
            return req_data.json()
        except:
            return {}


class AdminHandler(tornado.web.RequestHandler):
    @authenticated
    def get(self):
        ctx = {
            'static_url': settings.STATIC_URL,
            'token': self.get_argument('token', ''),
            'host': self.request.host,
            'version': settings.STATIC_VERSION,
            'SETTINGS': settings
        }
        self.render("admin.html", **ctx)


class RankHandler(tornado.web.RequestHandler):
    @authenticated
    def get(self):
        info = settings.rd.hgetall('WEIXIN_OPEN_INFO')
        user_info = {key: json.loads(value) for key, value in info.items()}

        data = get_rank(-1)
        for i in data:
            if i['name'] not in user_info:
                LOG.warning('user[%s] not in user_info %s, has been ignore', i['name'], user_info)
                continue
            i.update(user_info[i['name']])
        ctx = {'data': data, 'version': settings.STATIC_VERSION, 'static_url': settings.STATIC_URL, 'SETTINGS': settings}
        self.render("ranger4.html", **ctx)


class ErrorHandler(tornado.web.RequestHandler):
    @authenticated
    def get(self):
        message1, message2, button, url = u'场面太火爆', u'游戏服务器人员已满，请稍后重试！', u'我挤', '/rumpetroll/'
        tps = self.request.arguments.get("type", [])
        if tps and "server_error" == str(tps[0], 'utf-8'):
            message1, message2, button, url = u"服务器错误！", u"当前游戏服务出现问题，无法游玩。", u'重新登录', get_login_url(self.request)
        ctx = {
            'static_url': settings.STATIC_URL,
            'message1': message1,
            'message2': message2,
            'button': button,
            'url': url,
            'version': settings.STATIC_VERSION,
            'SETTINGS': settings,
        }
        self.render("error.html", **ctx)
