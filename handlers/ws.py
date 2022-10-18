# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
import json
import logging
import re
import time

import tornado.websocket

import settings
from common.manager import namespace
from common.structure import CloseData, InitData
from common.utils import object_to_json
from handlers.utils import status_uploader
from settings import OVERTIME, TOKEN

LOG = logging.getLogger(__name__)


class WSHandler(tornado.websocket.WebSocketHandler):
    _is_clean_gold = False
    # 状态
    # 0 开始
    # 1 发送测试金币
    # 2 测试结束，清空金币
    # 3 发送正式金币
    stage = 0

    def __init__(self, *args, **kwargs):
        super(WSHandler, self).__init__(*args, **kwargs)
        # Pending messages
        LOG.info('websocket request uri: %s', self.request.uri)
        self.pending_messages = []
        self._is_close = False
        self.is_messager = self.get_argument('messager', '0') == '1'
        self.namespace = self.request.headers.get('Namespace')
        self.room_num = self.get_room()
        self.room = self.room_num
        self._id = id(self)
        self.pipe = settings.rd.pipeline()

    def get_room(self):
        room_num = self.request.headers.get('Room')
        if room_num:
            LOG.info('get room num from header, %s', room_num)

        if not room_num:
            room_num = self.get_argument('room', None)
            if room_num:
                LOG.info('get room num from argument, %s', room_num)

        return room_num or '1'

    def get_current_user(self):
        cid = self.get_cookie('openid', None)
        return cid

    def on_pong(self, data):
        LOG.debug('client[%s] on_pong data: %s', self._id, data)

    def check_origin(self, origin):
        return True

    def broadcast(self, msg_type, message, room_num=None):
        try:
            if not room_num:
                room_num = self.room_num

            if msg_type == 'update':
                # # 需要重置蝌蚪大小
                # if WSHandler.stage == 2:
                #     # default size, in Tadpole.js
                #     _message['size'] = 3
                #     message = json.dumps(_message)
                for client in namespace.get_participants(room_num):
                    client.add_pending_message(message)
            else:
                for client in namespace.get_participants(room_num):
                    if not client._is_close:
                        client.write_message(message)
        except Exception:
            LOG.exception('broadcast error')

    ################################
    # Methods for pending messages #
    ################################

    PREFIX_MULTI_MESSAGES = '__mul__::'

    def add_pending_message(self, message):
        """Add pending message, then wait for periodic task to send back to client

        :param str message: message to send
        """
        self.pending_messages.append(message)

    def clean_pending_messages(self):
        self.pending_messages = []

    def send_pending_message(self):
        # TODO: Add mutex to let this become atomic
        if self.pending_messages and not self._is_close:
            self.write_message(self.PREFIX_MULTI_MESSAGES + '\n'.join(self.pending_messages))
            self.clean_pending_messages()

    def open(self, server=None, port=None):
        # 加豆子的客户端不需要初始化
        if self.is_messager:
            return

        namespace.enter_room(self)

        welcome = InitData(self._id)
        welcome.room_num = self.room_num

        self.write_message(object_to_json(welcome))
        self.write_message(self.golds)

        LOG.info('client[%s] has been opened, room: %s total: %s', self._id, self.room_num, namespace.stat['online'])

    def on_eat_gold(self, message):
        """处理吃豆子逻辑"""
        LOG.info('eat: %s' % message)
        openid = message.get('openid', None)
        # 身份不合法，豆子依然被吃掉，但是不计数排名
        if not openid:
            LOG.warning('invalid client[%s|%s] eat gold: %s, ignored', self._id, openid, message)
            return

        is_got = message.get('isGOT', False)
        name = message.get('name', '')

        tag = namespace.golds[message['goldId']]['tag']
        if tag == 'test':
            return

        room = namespace.golds[message['goldId']]['room']

        st = time.time()
        resp = (
            self.pipe.zincrby('rumpetroll::zs_eat_gold_counter', openid, 1)
            .hset('rumpetroll::h_eat_gold_timestamp', openid, time.time())
            .execute()
        )
        LOG.debug('client[%s|%s] eat gold: %.2fms, %s, %s', self._id, openid, (time.time() - st) * 1000, resp, message)

        # 处理排行榜
        namespace.incr_rank(openid, 1, name=name, is_got=is_got)

        # 处理豆子统计信息
        namespace.incr_gold('global', -1)
        namespace.incr_gold(room, -1)

        namespace.golds.pop(message['goldId'])

    def on_add_gold(self, message):
        token = message.get('token', '')
        if token != TOKEN:
            self.write_message(u'TOKEN不正确，不能修改gold！')
            return
        num = message.get('num', '')
        if not num:
            self.write_message(u'num参数不存在，不能修改gold！')
            return
        if not re.match(r'^[1-9]+[0-9]*$', str(num)):
            self.write_message(u'num参数必须是正整数，不能修改gold！')
            return

        num = int(num)
        is_test = message.get('test', False)
        if is_test:
            # 发送测试金币
            WSHandler.stage = 1
            LOG.debug('set stage to [%s]', WSHandler.stage)
        else:
            # 发送正式金币
            WSHandler.stage = 3
            LOG.debug('set stage to [%s]', WSHandler.stage)

        namespace.add_golds(num, is_test)

        new_loop = False
        if not namespace.marked_timestamp and not is_test:
            namespace.marked_timestamp = int(time.time() * 1000)
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.call_later(OVERTIME, clean_golds)
            new_loop = True

        self.write_message(u'添加%s个gold成功！' % num)
        for room in namespace.rooms:
            golds = dict(filter(lambda x: x[1]['room'] == room, namespace.golds.items()))
            _message = {
                'type': 'gold',
                'golds': golds,
                'timestamp': namespace.marked_timestamp,
                'is_created': True,
                'new_loop': new_loop,
                'test': is_test,
            }
            msg_type = 'gold'
            _message = json.dumps(_message)
            self.broadcast(msg_type, _message, room)

    def on_message(self, raw_message):
        try:
            message = json.loads(raw_message)
            msg_type = message.get('type')

            if message.get('type') == 'eatGold' and message.get('goldId') in namespace.golds:
                self.on_eat_gold(message)
                self.broadcast(msg_type, raw_message)

            elif message.get('type') == 'addGold':
                self.on_add_gold(message)

            else:
                self.broadcast(msg_type, raw_message)

        except Exception:
            LOG.exception('on_message error')

    @property
    def golds(self):
        golds = dict(filter(lambda x: x[1]['room'] == self.room_num, namespace.golds.items()))
        if namespace.marked_timestamp:
            new_loop = True
        else:
            new_loop = False
        message = {'type': 'gold', 'golds': golds, 'timestamp': namespace.marked_timestamp, 'new_loop': new_loop}
        return json.dumps(message)

    def on_close(self):
        self._is_close = True
        if self.is_messager:
            return

        message = object_to_json(CloseData(self._id))
        LOG.info(message)
        msg_type = 'closed'
        self.broadcast(msg_type, message)

        namespace.leave_room(self)

        LOG.info('client[%s] has been closed, room: %s remain: %s', self._id, self.room_num, namespace.stat['online'])


def send_message_to_clients():
    for client in namespace.clients:
        client.send_pending_message()


def send_ping_to_clients():
    for client in namespace.clients:
        client.ping('ping')


def update_node_status():
    status_uploader.upload_status(namespace.name, 'golds', namespace.golds_stat)
    status_uploader.upload_status(namespace.name, 'rank', namespace.rank)
    status_uploader.upload_status(namespace.name, 'online', namespace.stat)


def clean_golds():
    """清除豆子"""
    try:
        message = {'type': 'gold', 'golds': [], 'timestamp': namespace.marked_timestamp}
        message = json.dumps(message)

        for client in namespace.clients:
            client.write_message(message)

        for room in namespace.golds_stat:
            namespace.incr_gold(room, reset=True)

        namespace.golds.clear()
        namespace.marked_timestamp = None
        LOG.info('clean golds success')
    except Exception:
        LOG.exception('clean golds error')
