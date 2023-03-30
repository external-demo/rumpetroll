"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
# pylint: disable=broad-except
import datetime
import json
import logging
import re
import uuid

try:
    from cStringIO import StringIO
except ImportError:
    # py3
    from io import StringIO

    # py2
    # from StringIO import StringIO

import tornado.web
from tornado import gen

import settings
from auth import non_blocking as wx_client
from common import export, utils_func
from common.manager import NAMESPACE
from common.retrying import Retrying
from handlers import utils as handler_utils
from handlers.utils import authenticated, get_rank

LOG = logging.getLogger(__name__)


class APIHandler(tornado.web.RequestHandler):
    """
    api handler
    """

    def json_response(self, json_data):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(json_data))


class PingHandler(APIHandler):
    def get(self):
        self.set_header('Content-Type', 'text')
        self.write("pong")


class GetStatHandler(APIHandler):
    """
    A router view, send requests to every node which defined in settings,
    the merge result.
    """

    @authenticated
    def get(self):
        meter = self.get_argument('meter', '')
        detail = self.get_argument('detail', '0')
        responses = handler_utils.status_uploader.pull_all_statuses(meter)
        show_detail = detail == '1'

        if meter == 'rank':
            resp = self.merge_resp_rank()
        elif meter == 'golds':
            resp = self.merge_resp_golds(responses, show_detail)
        elif meter == 'online':
            resp = self.merge_resp_online(responses, show_detail)
        else:
            resp = {'data': [], 'result': False, 'message': u'meter is invalid'}
        self.json_response(resp)

    def merge_resp_rank(self):
        all_clients = settings.RD.hgetall('WEIXIN_OPEN_INFO')
        all_timestamps = settings.RD.hgetall('rumpetroll::h_eat_gold_timestamp')
        all_golds = dict(settings.RD.zrange('rumpetroll::zs_eat_gold_counter', 0, -1, withscores=True))
        data = {}
        for openid, info in all_clients.items():
            if not openid:
                continue

            golds = all_golds.get(openid, 0)
            if not golds:
                continue

            try:
                info = json.loads(info)
            except Exception:
                logging.exception('load info error: %s' % info)
                info = {}

            if not info or not info.get('nickname'):
                continue

            data[openid] = {'is_got': False, 'openid': str(openid, encoding="utf-8")}
            data[openid]['name'] = info['nickname']
            data[openid]['golds'] = golds
            data[openid]['last_time'] = str(all_timestamps.get(openid, None), encoding="utf-8")

        # data = data.values()
        result = []
        for item in data:
            result.append(data[item])

        return {
            'result': True,
            'message': u'获取排行统计成功',
            'data': result,
        }

    def merge_resp_golds(self, responses, show_detail):
        merged_data = {
            'remain': 0,
            'total': 0,
            'percent': 0,
        }

        for _, gold_stat in responses.items():
            merged_data['remain'] += gold_stat['global']['remain']
            merged_data['total'] += gold_stat['global']['total']
        if merged_data['total']:
            merged_data['percent'] += round(float(merged_data['remain']) / merged_data['total'], 4)
        else:
            merged_data['percent'] = 0
        if show_detail:
            merged_data.update(responses)

        return {
            'result': True,
            'message': u'获取金豆统计成功',
            'data': merged_data,
        }

    def merge_resp_online(self, responses, show_detail):
        peak_at = None
        online = 0
        peak = 0
        _namespaces = NAMESPACE.get_global_namespaces()
        for _namespace, stat in responses.items():
            if _namespace in _namespaces:
                online += stat['online']
                if stat['peak_at'] > peak_at:
                    peak_at = stat['peak_at']
                peak += stat['peak']

        merged_data = {
            'peak_at': peak_at,
            'online': online,
            'peak': peak,
        }
        if show_detail:
            merged_data.update(responses)

        return {
            'result': True,
            'message': u'获取在线统计成功',
            'data': merged_data,
        }


class GetUserHandler(APIHandler):
    """
    get user api
    """

    @authenticated
    def get(self):
        try:
            info = settings.RD.hgetall('WEIXIN_OPEN_INFO')
            data = {key: json.loads(value) for key, value in info.items()}
            result = {'result': True, 'message': '', 'data': data}
            self.json_response(result)
        except Exception as error:
            result = {'result': False, 'message': '%s' % error, 'data': None}
            self.json_response(result)


class RankDataHandler(APIHandler):
    """
    user api
    """

    @gen.coroutine
    @authenticated
    def get(self):
        data = get_rank(-1)
        if data:
            info = settings.RD.hgetall('WEIXIN_OPEN_INFO')
            user_info = {key: json.loads(value) for key, value in info.items()}
            for i in data:
                if i['name'] not in user_info:
                    LOG.warning('user[%s] not in user_info %s, has been ignore', i['name'], user_info)
                    continue
                i.update(user_info[i['name']])
        self.json_response(data)


class GoldsHandler(APIHandler):
    """
    golds api
    """

    @gen.coroutine
    @authenticated
    def get(self):
        num = self.get_argument('num', '')
        # test = self.get_argument('test', '0')  # noqa
        clean = self.get_argument('clean', '0')
        if clean == '1':
            try:
                handler_utils.clean_golds_client()
                result = {
                    'result': True,
                    'message': u"清除豆子成功",
                    'data': None,
                }
            except Exception as error:
                LOG.exception('clean_golds_client error')
                result = {
                    'result': False,
                    'message': error.message,
                    'data': None,
                }
            return self.json_response(result)

        if not num:
            result = {'message': u'num参数不存在', 'result': False, 'data': None}
            return self.json_response(result)

        if not re.match(r'^[1-9]+[0-9]*$', num):
            result = {'message': u'num参数必须是正整数', 'result': False, 'data': None}
            return self.json_response(result)

        try:
            handler_utils.add_golds_client(num, False)
            # 试玩需求
            # is_test = test == '1'
            # if is_test:
            #     handler_utils.add_golds_client(num, is_test)
            # else:
            #     handler_utils.add_golds_client_loop(num, False)
            result = {
                'result': True,
                'message': u"添加豆子成功",
                'data': None,
            }
        except Exception as error:
            LOG.exception("add_golds_client error")
            result = {
                'result': False,
                'message': error.message,
                'data': None,
            }
        return self.json_response(result)


class GetUserNameHandler(APIHandler):
    """
    get user name api
    """

    @gen.coroutine
    @authenticated
    def get(self):
        # gender 1为男性 2为女性 0为未知
        openid = self.get_cookie('openid', '')
        if not openid:
            data = {'is_got': False, 'name': 'Guest', 'gender': 1, 'openid': ''}
        elif openid == 'is__superuser':  # PC登入
            data = {'is_got': False, 'name': u"蓝鲸智云", 'gender': 2, 'openid': ''}
        else:
            try:
                gender = self.get_cookie('gender', '2')
                name, gender = yield wx_client.get_userinfo(openid, gender=gender)
                data = {'is_got': False, 'name': name, 'gender': gender, 'openid': openid}
            except Retrying:
                LOG.warning('Retrying GetUserName: %s', openid)
                try:
                    name, gender = yield wx_client.get_userinfo(openid, use_cache=False)
                    data = {'is_got': False, 'name': name, 'gender': gender, 'openid': openid}
                except Exception:
                    LOG.exception('Retrying GetUserName %s error', openid)
                    data = {'is_got': False, 'name': 'Guest', 'gender': '1', 'openid': openid}
            except Exception:
                LOG.exception('GetUserNameHandler %s error', openid)
                data = {'is_got': False, 'name': 'Guest', 'gender': '1', 'openid': openid}

        self.json_response(data)


class ExportHandler(APIHandler):
    """
    export api
    """

    @authenticated
    def get(self):
        num = self.get_argument('num', '20')
        if not re.match(r'^[1-9]+[0-9]*$', num):
            num = 20
        data = handler_utils.get_rank(int(num))
        header_list = [
            ('name', u"rtx名称"),
            ('golds', u"吃金币数"),
        ]
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.set_header('Content-Type', 'application/ms-excel')
        self.set_header(
            'Content-Disposition', "attachment; filename={}-{}.xls".format(u"运营部年会-统计排行".encode('utf-8'), now)
        )
        LOG.debug('export data: %s' % data)
        string_io = StringIO()
        string_io = export.export2excel(data, header_list, string_io)
        self.write(string_io.getvalue())
        string_io.close()


class GetEndpointHandler(APIHandler):
    """
    endpoint api
    """

    @authenticated
    def get(self):
        try:
            _namespace, room, cid = NAMESPACE.find_best_room()
            endpoint = self.get_endpoint(self.request, _namespace, room, cid)
            data = {'result': True, 'data': {'endpoint': endpoint}, 'message': u"获取endpoint成功"}
        except ValueError as error:
            data = {'result': False, 'data': {'endpoint': ''}, 'message': '%s' % error}
        self.json_response(data)

    @staticmethod
    def get_endpoint(request, _namespace, room, cid):
        """Get websocket url from node host"""
        sid = uuid.uuid4().hex
        server, port = _namespace.split(':')
        server_id = server.split('.')[-1]
        ctx = {
            'HOST': request.host,
            'server_id': server_id,
            'port': port,
            'room': room,
            'sid': sid,
            'cid': cid,
            'ws': settings.WSS,
        }
        ws_url = '{ws}://{HOST}/rumpetroll/socket.io/{server_id}/{port}/?room={room}&sid={sid}&cid={cid}'.format(**ctx)
        return ws_url


class FunctionController(APIHandler):
    """功能开关API"""

    @authenticated
    def get(self):
        func_code = self.get_argument('func_code', '')
        if not func_code:
            data = {'result': True, 'data': {}, 'message': u'参数【func_code】不能为空'}
        else:
            data = utils_func.get_func_control(func_code)
            data = {'result': True, 'data': data, 'message': u"获取成功"}
        self.json_response(data)

    @authenticated
    def post(self):
        """Get websocket url from node host"""
        func_code = self.get_body_argument('func_code', '')
        if not func_code:
            data = {'result': True, 'data': {}, 'message': u'参数【func_code】不能为空'}
            return self.json_response(data)

        enabled = self.get_body_argument('enabled', '')
        if not enabled:
            data = {'result': True, 'data': {}, 'message': u'参数【enabled】不能为空'}
            return self.json_response(data)

        enabled = enabled != '0'

        wlist = self.get_body_argument('wlist', '')
        if wlist:
            wlist = [i.strip() for i in wlist.split(';') if i]
        else:
            wlist = []

        func_name = self.get_body_argument('func_name', '')
        utils_func.set_func_control(func_code, func_name, enabled, wlist)
        data = {'result': True, 'data': {}, 'message': u'设置成功'}
        self.json_response(data)


class CleanHandler(APIHandler):
    """清楚数据开关"""

    KEY_PREFIX = 'rumpetroll::*'
    REDIS_KEYS = [
        "rumpetroll::h_eat_gold_timestamp",
        "rumpetroll::zs_eat_gold_counter",
    ]

    @authenticated
    def post(self):
        _data = {}
        for key in self.REDIS_KEYS:
            _data[key] = settings.RD.delete(key)
        data = {'result': True, 'data': _data, 'message': u'redis清理成功'}
        self.json_response(data)
