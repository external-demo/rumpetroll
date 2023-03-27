"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import datetime
import json
import logging
import random
import time

from tornado.options import options

import settings

LOG = logging.getLogger(__name__)


class Namespace(object):
    """
    room is a num，str type
    """

    # namespace节点信息
    RK_NAMESPACE_KEY = 'rumpetroll::namespace'
    RK_NAMESPACE_HEARTBEAT_KEY = 'rumpetroll::namespace::heartbeat'

    # room信息
    RK_ROOM_CLIENTS_COUNTER_KEY = 'rumpetroll::room::client_counter'
    RK_ROOM_NAMESPACK_KEY = 'rumpetroll::room::namespace'

    def __init__(self, redisdb):
        self.redisdb = redisdb
        self.host = options.address
        self.port = options.port
        self.name = f'{self.host}:{self.port}'
        self.pipeline = redisdb.pipeline()

        self.rooms = {}
        self.stat = {'peak': 0, 'peak_at': 0, 'online': 0}

        self.golds = {}
        self.golds_stat = {'global': {'total': 0, 'remain': 0, 'percent': 0}}
        # 发送豆子时间戳
        self.marked_timestamp = None

        # 吃豆子排名信息
        self.rank = {}

    def heartbeat(self, verbose=False):
        """
        function
        """
        current_time = time.time()

        # 存活信息
        self.pipeline.zadd(self.RK_NAMESPACE_HEARTBEAT_KEY, self.name, time.time())

        # 同步节点(namespace)信息
        self.pipeline.hset(self.RK_NAMESPACE_KEY, self.name, self.status)

        # 同步房间client数量
        # 接入层完成，同步会稍微影响计数
        self.pipeline.execute()

        self.heartbeat_clean()

        if verbose:
            LOG.debug('heartbeat finish in %.3f(ms)', (time.time() - current_time) * 1000)

    def heartbeat_clean(self):
        """
        clean
        """
        _alive_namespaces = self.get_alive_namespaces()

        # 清空非存活的namespace
        _namespaces = self.redisdb.hgetall(self.RK_NAMESPACE_KEY)
        _dead_namespace = set()
        for namespace in _namespaces:
            if namespace not in _alive_namespaces:
                _dead_namespace.add(namespace)
        if _dead_namespace:
            LOG.warning('heartbeat clean dead namespace: %s', _dead_namespace)
            self.pipeline.hdel(self.RK_NAMESPACE_KEY, *_dead_namespace)

        # 清空非存活的房间计数数据
        _dead_room = set()
        _expire_room = set()
        rooms = self.redisdb.zrange(self.RK_ROOM_CLIENTS_COUNTER_KEY, 0, -1)
        room_namespace = self.redisdb.hgetall(self.RK_ROOM_NAMESPACK_KEY)
        for room in rooms:
            _namespace = room_namespace.get(room)
            # 清空已经挂了的进程房间
            if _namespace and _namespace not in _alive_namespaces:
                _dead_room.add(room)
            # 清空进程重启后，房间不同步的房间
            if _namespace == self.name and room not in self.rooms:
                _expire_room.add(room)

        if _dead_room or _expire_room:
            LOG.warning('heartbeat clean dead room: %s, expire room: %s', _dead_room, _expire_room)
            self.pipeline.zrem(self.RK_ROOM_CLIENTS_COUNTER_KEY, *_dead_room.union(_expire_room))
            self.pipeline.hdel(self.RK_ROOM_NAMESPACK_KEY, *_dead_room.union(_expire_room))

        self.pipeline.execute()

    def get_alive_namespaces(self):
        """获取存活节点"""
        now = time.time()
        start = now - 2
        end = now + 2
        _namespaces = self.redisdb.zrangebyscore(self.RK_NAMESPACE_HEARTBEAT_KEY, start, end)
        return _namespaces

    @property
    def clients(self):
        """获取全部clients"""
        for client_set in self.rooms.values():  # itervalues():
            for client in client_set:
                yield client

    def get_participants(self, room):
        """Return an iterable with the active participants in a room."""
        for client in self.rooms[room]:
            yield client

    def get_global_namespaces(self):
        """获取全局namespace"""
        ret = self.redisdb.hgetall(self.RK_NAMESPACE_KEY)
        return {str(key, "utf-8"): json.loads(value) for key, value in ret.items()}

    def update_stat(self):
        """
        function
        """
        self.stat['online'] = len(list(self.clients))
        if self.stat['online'] > self.stat['peak']:
            self.stat['peak'] = self.stat['online']
            self.stat['peak_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            LOG.info('new peak: %s', self.stat['peak'])

    def enter_room(self, client):
        """
        function
        """
        LOG.debug('clients enter room, client=%s, room=%s, user=%s',
                  client,
                  client.room,
                  client.current_user)

        if client.room not in self.rooms:
            self.rooms[client.room] = set()
        self.rooms[client.room].add(client)
        self.update_stat()

    def leave_room(self, client):
        """Remove a client from a room."""
        LOG.debug('clients leave room, client=%s, room=%s, user=%s',
                  client,
                  client.room,
                  client.current_user)

        try:
            self.rooms[client.room].remove(client)
            self.update_stat()
        except KeyError:
            LOG.exception('leave room error, rooms:%s, room:%s, client:%s',
                          self.rooms,
                          client.room,
                          client)

        return self.redisdb.zincrby(self.RK_ROOM_CLIENTS_COUNTER_KEY, client.room, -1)

    @property
    def status(self):
        """
        function
        """
        data = json.dumps(self.rooms, cls=NamespaceEncoder)
        return data

    def incr_gold(self, room='global', count=-1, reset=False):
        """
        游戏相关处理逻辑
        """
        if room not in self.golds_stat:
            self.golds_stat[room] = {'total': 0, 'remain': 0, 'percent': 0}

        stat = self.golds_stat[room]

        if reset:
            stat['remain'] = 0
            stat['total'] = 0
            stat['percent'] = 0
            return True

        for counter in ['total', 'remain']:
            # 总数不减
            if counter == 'total' and count < 0:
                continue

            stat[counter] += count
            if stat[counter] < 0:
                stat[counter] = 0

        if stat['total'] > 0:
            stat['percent'] = round(stat['remain'] * 1.0 / stat['total'], 4)

    def incr_rank(self, user_id, count, **kwargs):
        """
        function
        """
        if user_id in self.rank:
            _rank = self.rank[user_id]
        else:
            _rank = {'golds': 0}
        _rank.update(kwargs)
        _rank['golds'] += count
        _rank['last_time'] = time.time()
        _rank['openid'] = user_id

        self.rank[user_id] = _rank

    def add_golds(self, num=10, is_test=False):
        """添加金币"""
        tag = 'test' if is_test else 'prod'
        for room in self.rooms:
            for gold in smoothness_rand_gold(num, room=room, tag=tag):
                self.golds[gold['goldId']] = gold
                self.incr_gold('global', 1)
                self.incr_gold(room, 1)
        if self.rooms:
            LOG.info('add %s golds with tag=%s to rooms: %s', num, tag, self.rooms.keys())
        else:
            LOG.info('has no active rooms, just ignored')


class NamespaceEncoder(json.JSONEncoder):
    """
    namespace encode
    """

    def default(self, obj):
        if isinstance(obj, set):
            return [i._id for i in obj]
        return json.JSONEncoder.default(self, obj)


NAMESPACE = Namespace(settings.RD)


def smoothness_rand_gold(num, **kwargs):
    """给房间填充金币算法
    1, 平均分区块
    2, 区块内随机分布金币
    """

    # 计算每个格子里面多少个豆子
    num_box = num // settings.DIVISION_OF_MATRIX ** 2
    num_box = [num_box] * settings.DIVISION_OF_MATRIX ** 2
    num_box[-1] += num % settings.DIVISION_OF_MATRIX ** 2

    # 计算每个格子坐标范围
    m_step = (settings.MAX_OF_MATRIX - settings.MIN_OF_MATRIX) / settings.DIVISION_OF_MATRIX
    _remain = (settings.MAX_OF_MATRIX - settings.MIN_OF_MATRIX) % settings.DIVISION_OF_MATRIX
    divisions = []  # noqa
    for division_y in range(settings.DIVISION_OF_MATRIX):
        for division_x in range(settings.DIVISION_OF_MATRIX):
            divisions.append({
                'x_min': settings.MIN_OF_MATRIX + division_x * m_step,
                'x_max': settings.MIN_OF_MATRIX + (division_x + 1) * m_step,
                'y_min': settings.MAX_OF_MATRIX - (division_y + 1) * m_step,
                'y_max': settings.MAX_OF_MATRIX - division_y * m_step,
            })
        # 补最后空余坐标
        divisions[-1]['x_max'] += _remain
    for division in range(1, settings.DIVISION_OF_MATRIX + 1):
        divisions[-division]['y_min'] -= _remain

    for idx, num_golds in enumerate(num_box):
        for num_glod in range(num_golds):
            print(num_glod)
            key = random.randint(100000000, 999999999)
            box = divisions[idx]
            # 金币对象
            gold = {
                'x': random.randrange(box['x_min'], box['x_max']),
                'y': random.randrange(box['y_min'], box['y_max']),
                'goldId': key,
            }
            # 添加任意字段
            gold.update(kwargs)
            yield gold
