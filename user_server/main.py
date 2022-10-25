# user login and register model
import os
os.environ["MODULE"] = "USER_SERVER"
import logging
import tornado.ioloop as ioloop
import tornado.httpserver as httpserver
import tornado.web as web
from urls import handlers
from settings_user_server import settings


class Application(web.Application):
    def __init__(self):
        web.Application.__init__(self, handlers, **settings)


LOG = logging.getLogger(__name__)
main_loop = ioloop.IOLoop.instance()


def main():
    http_server = httpserver.HTTPServer(Application())
    http_server.listen(settings.get("port"))
    main_loop.start()


if __name__ == '__main__':
    LOG.info("register server start")
    main()
