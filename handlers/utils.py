# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
import json
import logging
import os.path
import time
from functools import wraps

import tornado.ioloop
from tornado import gen
from tornado.websocket import websocket_connect

import settings
from common.manager import NAMESPACE
from common.utils_func import func_control
from settings import RD

LOG = logging.getLogger(__name__)


class NodeDispatcher(object):
    """Dispatcher, determine client should connect to which client"""

    RK_CLIENTS_COUNTER = 'rumpetroll::zs_clients_counter'

    def __init__(self, redisdb):
        self.redisdb = redisdb
        self.max_clients_per_node = settings.MAX_ROOM_SIZE * settings.MAX_ROOM

    def client_enter(self, node_name):
        LOG.debug('Incr clients count for node_name=%s', node_name)
        return self.redisdb.zincrby(self.RK_CLIENTS_COUNTER, node_name, 1)

    def client_exit(self, node_name):
        LOG.debug('Decr clients count for node_name=%s', node_name)
        return self.redisdb.zincrby(self.RK_CLIENTS_COUNTER, node_name, -1)

    def try_enter(self, node_name):
        """Try to enter, will exit any way"""
        future_cnt = self.client_enter(node_name)
        self.client_exit(node_name)
        return future_cnt

    def force_update_count(self, node_name, count):
        return self.redisdb.zadd(self.RK_CLIENTS_COUNTER, node_name, count)

    def find_best_node(self):
        current_time = time.time()
        online_counts = self.redisdb.zrange(self.RK_CLIENTS_COUNTER, 0, -1, withscores=True)
        online_counts = dict(online_counts)

        # Find the most suitable node in the first place
        LOG.info('settings.NODE_HOSTS: %s', settings.NODE_HOSTS)
        client_counts = [(x['name'], online_counts.get(x['name'], 0)) for x in settings.NODE_HOSTS]
        LOG.debug('Finding best node, client_counts=%s' % client_counts)
        for node_name, cnt in client_counts:
            if cnt >= self.max_clients_per_node:
                continue

            # Try enter, if fail, use next node instead
            # Will resotre count anyway
            if self.try_enter(node_name) > self.max_clients_per_node:
                LOG.debug('Try entering node_name=%s, failed, will try next...' % node_name)
                continue
            LOG.debug('Found best node %.2fms, node_name=%s',
                      (time.time() - current_time) * 1000,
                      node_name
                      )
            return node_name
        else:
            LOG.error('All available nodes tried, can not found vacant one.')
            raise ValueError(u"游戏服务器人员已满，请稍后重试！")


node_dispatcher = NodeDispatcher(RD)


class StatusUploader(object):
    """Upload every status to redis"""

    RK_STATUS_TMPL = 'rumpetroll::zs_nodes_status::%s'

    def __init__(self, redisdb):
        self.redisdb = redisdb

    def upload_status(self, node_name, type, value):
        key = self.RK_STATUS_TMPL % type
        return self.redisdb.hset(key, node_name, json.dumps(value))

    def pull_all_statuses(self, type):
        key = self.RK_STATUS_TMPL % type
        ret = self.redisdb.hgetall(key)
        return {key: json.loads(value) for key, value in ret.items()}


status_uploader = StatusUploader(RD)


@gen.coroutine
def add_golds_client_loop(num, test=False):
    io_loop = tornado.ioloop.IOLoop.current()
    for i in range(6):
        io_loop.call_later(i * 30, add_golds_client, num, test)


@gen.coroutine
def add_golds_client(num, test=False):
    _namespaces = NAMESPACE.get_global_namespaces()
    for node in _namespaces:
        url = '%s://%s/rumpetroll/socket.io/?messager=1&room=1' % (settings.WSS, node)
        LOG.debug('send add golds message to %s', url)
        conn = yield websocket_connect(url)
        message = {'type': 'addGold', 'num': num, 'token': settings.TOKEN, 'test': test}
        conn.write_message(json.dumps(message))
        conn.close()
    LOG.info('add_golds_client add [%s] golds success' % num)


@gen.coroutine
def clean_golds_client():
    """清除豆子"""
    _namespaces = NAMESPACE.get_global_namespaces()
    for node in _namespaces:
        url = '{0}://{1}/rumpetroll/{2}/ws?messager=1'.format(settings.WSS,
                                                              settings.HOST,
                                                              node['url'].split(':')[-1]
                                                              )
        LOG.debug('send clean golds message to %s', url)
        conn = yield websocket_connect(url)
        message = {'type': 'cleanGold', 'token': settings.TOKEN}
        conn.write_message(json.dumps(message))
        conn.close()
    LOG.info('clean golds success')


def get_rank(num):
    """获取排名"""
    statuses = status_uploader.pull_all_statuses('rank')
    responses = statuses.values()
    merged_data = {}
    for data in responses:
        if data:
            for openid, _data in data.items():
                if openid not in merged_data:
                    merged_data[openid] = _data
                else:
                    merged_data[openid]['golds'] += _data['golds']
    data = merged_data.values()
    LOG.debug('get_rank raw data: %s  num: %s', data, num)
    data = filter(lambda x: x.get('name') not in settings.IGNORES_LIST, data)
    LOG.debug('IGNORES_LIST data: %s', data)

    # 时间最大值
    bigest_time = time.time() * 1000

    data = sorted(data, key=lambda x: (x.get('golds', 0), -x.get('last_time', bigest_time)), reverse=True)[:20]
    LOG.debug('rank data data: %s', data)
    return data


def authenticated(view_func):
    """权限认证装饰器"""

    @wraps(view_func)
    def _wrapped_view(self, *args, **kwargs):
        # 调用判断权限的方法
        token = self.get_argument("token", None)
        if token == settings.TOKEN:
            return view_func(self, *args, **kwargs)
        else:
            result = {'result': False, 'message': 'Token is invalid', 'data': None}
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(result))
            return

    return _wrapped_view


def is_started(view_func):
    """是否开启"""

    @wraps(view_func)
    def _wrapped_view(self, *args, **kwargs):
        openid = self.get_cookie('openid', '')
        token = self.get_argument('token', '')

        enabled, wlist = func_control('is_start')
        if not (enabled or openid in wlist or token == settings.TOKEN):
            ctx = {'static_url': settings.STATIC_URL, 'version': settings.STATIC_VERSION, 'SETTINGS': settings}
            self.render("start.html", **ctx)
            raise gen.Return()
        view_func(self, *args, **kwargs)

    return _wrapped_view


def check_white(open_id):
    if open_id == 'is__superuser':
        return True
    if not open_id:
        return False
    try:
        name, department = [], []
        with open(os.path.join(settings.BASE_DIR, 'etc/name.csv'), encoding='utf-8') as name_file:
            name = name_file.read().splitlines()

        with open(os.path.join(settings.BASE_DIR, 'etc/department.csv'), encoding='utf-8') as department_file:
            department = department_file.read().splitlines()

        department = dict(i.split(',')[::-1] for i in department)
        rtx = department.get(open_id)
        if rtx in name:
            LOG.debug('check_white OK, %s', rtx)
            return True
        else:
            LOG.warning('check_white Failed, %s', rtx)
            return False
    except FileExistsError:
        LOG.exception('check_white error, %s', open_id)
        return False
