# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
# pylint: disable=broad-except,R1720
import base64
import json
import logging

import tornado.web
from httpx import post
from tornado import gen

import settings
from auth import non_blocking as wx_client
from auth import utils as wx_utils
from handlers import utils as handlers_utils
from handlers.utils import authenticated, get_rank, is_started

LOG = logging.getLogger(__name__)


def get_login_url(request):
    return 'http://%s/rumpetroll/login/' % request.host


def get_register_url(request):
    return 'http://%s/rumpetroll/register/' % request.host


def get_register_server_url():
    return "http://{host}:{port}/register".format(host=settings.USER_SERVER_HOST, port=settings.PORT)


def get_login_server_url():
    return "http://{host}:{port}/login".format(host=settings.USER_SERVER_HOST, port=settings.PORT)


def get_websocket_url(request):
    return '%s://%s/rumpetroll/socket.io/' % (settings.WSS, request.host)


class LoginRegister():
    @staticmethod
    def login(data: dict) -> dict:
        try:
            req_data = post(url=get_login_server_url(), json=data, verify=False, timeout=60)
            return req_data.json()
        except BaseException: # noqa
            return {}

    @staticmethod
    def register(data: dict) -> dict:
        try:
            rep_data = post(url=get_register_server_url(), json=data, verify=False, timeout=30)
            return rep_data.json()
        except BaseException: # noqa
            return {}


class IndexHandler(tornado.web.RequestHandler):
    """
    index api
    """

    @gen.coroutine
    @is_started
    @tornado.web.addslash
    def get(self):
        openid = self.get_cookie('openid', '')

        token = self.get_argument('token', '')
        is_token = 0
        if token == settings.TOKEN:
            openid = self.get_argument('openid', 'is__superuser')
            gender = self.get_argument('gender', '1')
            is_token = 1
            self.set_cookie('openid', openid)
            self.set_cookie('gender', gender)

        elif openid == '':
            self.set_header('X-Frame-Options', 'DENY')
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
    """
    login api
    """

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
                self.set_header('X-Frame-Options', 'DENY')
                self.redirect(location)
                raise gen.Return()
            else:
                ctx = {
                    'static_url': settings.STATIC_URL,
                    'message': u"登录已经失效，请刷新后重试！",
                    'SETTINGS': settings
                }
                self.render("wx_error.html", **ctx)
                raise gen.Return()

        elif not state:
            self.set_header('X-Frame-Options', 'DENY')
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


class RegisterHandler(tornado.web.RequestHandler, LoginRegister):
    """
    register api
    """

    @gen.coroutine
    @is_started
    def get(self):
        ctx = {
            'static_url': settings.STATIC_URL,
            'version': settings.STATIC_VERSION,
            'SETTINGS': settings,
        }
        self.render("register.html", **ctx)

    def post(self):
        location = 'http://%s/rumpetroll/' % self.request.host
        register_location = 'http://{}/rumpetroll/register/'.format(self.request.host)
        error_location = "http://{0}/rumpetroll/error/".format(self.request.host)

        username = self.get_argument('username')
        gender = self.get_argument('gender')

        if username and (len(username) >= 1) and (gender in ['1', '2']):
            register_res = self.register({
                "username": username,
                "gender": gender
            })
            if not register_res:
                location = error_location + "?type=register_server_error&token={0}".format(
                    settings.TOKEN
                )
            elif not register_res.get("status", False):
                location = error_location + "?type=register_error&token={0}".format(
                    settings.TOKEN
                )
        else:
            location = register_location
        self.set_header('X-Frame-Options', 'DENY')
        self.redirect(location)


class LoginHandler(tornado.web.RequestHandler, LoginRegister):
    """
    login api
    """

    @gen.coroutine
    @is_started
    def get(self):
        # 已经验证用户先登出，再跳转
        self.clear_cookie('openid')
        self.clear_cookie('gender')
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
        data = {
            "username": username,
            "gender": gender
        }
        if username and (len(username) >= 1) and (gender in ['1', '2']):
            login_res = self.login(data)
            if not login_res:
                location = "http://{0}/rumpetroll/error/?type=server_error&token={1}".format(
                    self.request.host, settings.TOKEN)
            elif not login_res.get("status", False) and ("Name is registered" != login_res.get("result")):
                register_state = self.register(data)
                if not register_state:
                    location = "http://{0}/rumpetroll/error/?type=login_error&token={1}".format(
                        self.request.host, settings.TOKEN
                    )
                else:
                    openid = base64.b64encode(username.encode('utf-8'))
                    self.set_cookie('openid', openid)
                    self.set_cookie('gender', login_res.get("gender", gender))
            else:
                openid = base64.b64encode(username.encode('utf-8'))
                is_online = settings.RD.hget('rumpetroll::user_online', openid)
                is_online = int(is_online) if is_online else 0
                if is_online:
                    self.clear_cookie('openid')
                    self.clear_cookie('gender')
                    location = "http://{0}/rumpetroll/error/?type=notallow_login&token={1}".format(
                        self.request.host, settings.TOKEN)
                else:
                    self.set_cookie('openid', openid)
                    self.set_cookie('gender', login_res.get("gender", gender))
                    handlers_utils.add_golds_client(300)
                    LOG.debug(f'Login Success: {username}. add golds 300')
        else:
            location = '{}?next=http://{}/rumpetroll/'.format(
                get_login_url(self.request),
                self.request.host
            )
        self.set_header('X-Frame-Options', 'DENY')
        self.redirect(location)


class AdminHandler(tornado.web.RequestHandler):
    """
    admin api
    """

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
    """
    rank api
    """

    @authenticated
    def get(self):
        info = settings.RD.hgetall('WEIXIN_OPEN_INFO')
        user_info = {key: json.loads(value) for key, value in info.items()}

        data = get_rank(-1)
        for i in data:
            if i['name'] not in user_info:
                LOG.warning('user[%s] not in user_info %s, has been ignore', i['name'], user_info)
                continue
            i.update(user_info[i['name']])
        ctx = {
            'data': data,
            'version': settings.STATIC_VERSION,
            'static_url': settings.STATIC_URL,
            'SETTINGS': settings}
        self.render("ranger4.html", **ctx)


class ErrorHandler(tornado.web.RequestHandler):
    """
    error message
    """

    @authenticated
    def get(self):
        message1, message2, button, url = u'场面太火爆', u'游戏服务器人员已满，请稍后重试！', u'我挤', '/rumpetroll/'
        tps = self.get_query_argument("type", "")
        if tps:
            if "login_error" == tps:
                message1, message2, button, url = u"登录错误！", \
                                                  u'无当前用户名。', \
                                                  u'重新登录或注册', \
                                                  get_login_url(self.request)
            elif "server_error" == tps:
                message1, message2, button, url = u"登录服务错误！", \
                                                  u"当前游戏服务出现问题，无法登录。", \
                                                  u'重新登录', \
                                                  get_login_url(self.request)
            elif "register_server_error" == tps:
                message1, message2, button, url = u"注册服务错误！", \
                                                  u"当前游戏服务出现问题，无法注册。", \
                                                  u'重新注册', get_register_url(self.request)
            elif "register_error" == tps:
                message1, message2, button, url = u"注册错误！", \
                                                  u'用户名已被注册不可用。', \
                                                  u'重新注册', \
                                                  get_register_url(self.request)
            elif "secondpwd_notexists" == tps:
                message1, message2, button, url = u"注册错误！", \
                                                  u'两次输入的密码不一致。', \
                                                  u'重新注册', \
                                                  get_register_url(self.request)
            elif "inuse_username" == tps:
                message1, message2, button, url = u"注册错误！", \
                                                  u"用户名已被注册，可直接登录。", \
                                                  u'重新登录', \
                                                  get_login_url(self.request)
            elif "notallow_login" == tps:
                message1, message2, button, url = u"登录错误！", \
                                                  u"当前游戏用户已在线，请重新使用新游戏用户登录。", \
                                                  u'重新登录', \
                                                  get_login_url(self.request)

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
