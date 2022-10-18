# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
import logging
import logging.config
import os
import os.path

import redis
from dogpile.cache import make_region
from tornado.options import define, options

PORT = 20000

define("port", default=PORT, help="run on the given port", type=int)
define("address", default="127.0.0.1", help="bind address", type=str)
options.parse_command_line()

LOG = logging.getLogger(__name__)

# RUN_MODE DEVELOP PRODUCTION
RUN_MODE = os.environ.get('RUN_MODE', 'DEVELOP')

# 排名名单忽略列表
IGNORES_LIST = os.environ.get('IGNORES_LIST', [u'蓝鲸智云', 'Guest', 'guest'])


# 单房间最多连接数
MAX_ROOM_SIZE = int(os.environ.get('MAX_ROOM_SIZE', 3))
# 单进程最多房间数
MAX_ROOM = int(os.environ.get('MAX_ROOM', 1))

# 单进程最多房间数
ROOM_CLIENTS = int(os.environ.get('ROOM_CLIENTS', 3))


# 豆子分配区域
MIN_OF_MATRIX = int(os.environ.get('MIN_OF_MATRIX', -1000))
MAX_OF_MATRIX = int(os.environ.get('MAX_OF_MATRIX', 1000))
DIVISION_OF_MATRIX = int(os.environ.get('DIVISION_OF_MATRIX', 4))

# 豆子持续时间
OVERTIME = int(os.environ.get('OVERTIME', 60))

STATIC_VERSION = os.environ.get('STATIC_VERSION', 11)

BASE_DIR = os.path.dirname(__file__)


TOKEN = 'tPp5GwAmMPIrzXhyyA8X'
DEBUG = False


HTTP_PROXY = {}

SITE_URL = '/rumpetroll/'
STATIC_URL = '/rumpetroll/'
# 回调URL
DEBUG = True
DEFAULT_LOG_LEVEL = 'DEBUG'

# 看网络是否需要代理访问API
# HTTP_PROXY = {
#     'proxy_host': '10.135.21.238',
#     'proxy_port': 13128
# }

LOG_FILE = os.environ.get('LOG_FILE', '/tmp/rumpetroll.log')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
rd = redis.Redis(connection_pool=pool)

NAMESPACE_NAME = '{}:{}'.format(options.address, options.port)

region = make_region().configure(
    'dogpile.cache.redis',
    expiration_time=7200,
    arguments={
        'connection_pool': pool,
    },
)

# 模板title
TITLE = u"BlueKing"

# 认证模块
AUTH_MODULE = os.environ.get('AUTH_MODULE', 'dummy')

settings = dict(
    template_path=os.path.join(BASE_DIR, "templates"),
    static_path=os.path.join(BASE_DIR, "static"),
    xsrf_cookies=False,
    cookie_secret="bb904fe1b095cab9499a85f864e6c612",
    port=PORT,
    debug=DEBUG,
)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] {NAMESPACE_NAME} %(levelname)s  %(name)s: %(message)s'.format(
                **{'NAMESPACE_NAME': NAMESPACE_NAME}
            )  # noqa
        }
    },
    'handlers': {
        'console_simple': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_simple': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': LOG_FILE,
        },
    },
    'loggers': {
        'tornado': {
            'handlers': ['console_simple'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console_simple'],
    },
}

if not DEBUG:
    LOGGING_CONFIG['root']['handlers'] = ['file_simple']
    LOGGING_CONFIG['loggers']['tornado']['handlers'] = ['file_simple']

logging.config.dictConfig(LOGGING_CONFIG)
