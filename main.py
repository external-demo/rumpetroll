# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: Joe Lei <joelei@tencent.com>
import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import options

import settings
from common.manager import namespace
from handlers.ws import (
    send_message_to_clients,
    send_ping_to_clients,
    update_node_status,
)
from urls import handlers

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, handlers, **settings.settings)


# Scheduler start

# 1000ms / 24fps
interval_ms = 42

main_loop = tornado.ioloop.IOLoop.instance()
scheduler = tornado.ioloop.PeriodicCallback(send_message_to_clients, interval_ms, io_loop=main_loop)
scheduler.start()

# 不让自动断开，默认2分钟没有任何数据交互会断开
ping_interval_ms = 10 * 1000
ping_scheduler = tornado.ioloop.PeriodicCallback(send_ping_to_clients, ping_interval_ms, io_loop=main_loop)
ping_scheduler.start()


# Scheduler for node status
scheduler_node_status = tornado.ioloop.PeriodicCallback(update_node_status, 1000, io_loop=main_loop)
scheduler_node_status.start()


# Scheduler for namespace heartbeat
scheduler_namespace = tornado.ioloop.PeriodicCallback(namespace.heartbeat, 1000, io_loop=main_loop)
scheduler_namespace.start()


def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address=options.address)
    main_loop.start()


def main_process():
    options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.bind(options.PORT)
    http_server.start(0)  # forks one process per cpu
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    LOG.info('rumpetroll start')
    main()
