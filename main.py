"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import options

import settings
from common.manager import NAMESPACE
from handlers.ws import (
    send_message_to_clients,
    send_ping_to_clients,
    update_node_status,
)
from urls import handlers

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    """
    应用入口
    """

    def __init__(self):
        tornado.web.Application.__init__(self, handlers, **settings.SETTINGS)
        user_online_key = "rumpetroll::user_online"
        for user in settings.RD.hgetall(user_online_key):
            settings.RD.hset(user_online_key, user, 0)

# Scheduler start


# 1000ms / 24fps
INTERVAL_MS = 42

MAIN_LOOP = tornado.ioloop.IOLoop.instance()
SCHEDULER = tornado.ioloop.PeriodicCallback(send_message_to_clients, INTERVAL_MS, io_loop=MAIN_LOOP)
SCHEDULER.start()

# 不让自动断开，默认2分钟没有任何数据交互会断开
PING_INTERVAL_MS = 10 * 1000
PING_SCHEDULER = tornado.ioloop.PeriodicCallback(
    send_ping_to_clients,
    PING_INTERVAL_MS,
    io_loop=MAIN_LOOP
)
PING_SCHEDULER.start()

# Scheduler for node status
SCHEDULER_NODE_STATUS = tornado.ioloop.PeriodicCallback(update_node_status, 1000, io_loop=MAIN_LOOP)
SCHEDULER_NODE_STATUS.start()

# Scheduler for namespace heartbeat
SCHEDULER_NAMESPACE = tornado.ioloop.PeriodicCallback(NAMESPACE.heartbeat, 1000, io_loop=MAIN_LOOP)
SCHEDULER_NAMESPACE.start()


def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address=options.address)
    MAIN_LOOP.start()


def main_process():
    options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.bind(options.PORT)
    http_server.start(0)  # forks one process per cpu
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    LOG.info('rumpetroll start')
    main()
