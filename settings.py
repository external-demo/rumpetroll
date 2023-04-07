"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import logging
import logging.config
import os
import os.path

import redis
from dogpile.cache import make_region
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tornado.options import define, options

# 组件标识
MODULE = os.environ.get("MODULE")
PORT = 20000
USER_SERVER_PORT = 30000
SERVICE_SERVER_PORT = 40000
USER_SERVER_HOST = os.environ.get("USER_SERVER_HOST", "127.0.0.1")
SERVICE_SERVER_HOST = os.environ.get("SERVICE_SERVER_HOST", "127.0.0.1")
HOST = os.environ.get("HOST", "127.0.0.1")

if MODULE == "USER_SERVER":
    PORT = 30000
elif MODULE == "SERVICE_SERVER":
    PORT = 40000
define("port", default=PORT, help="run on the given port", type=int)
define("address", default=HOST, help="bind address", type=str)
options.parse_command_line()

LOG = logging.getLogger(__name__)

# RUN_MODE DEVELOP PRODUCTION
RUN_MODE = os.environ.get('RUN_MODE', 'DEVELOP')

# 排名名单忽略列表
IGNORES_LIST = os.environ.get('IGNORES_LIST', [u'蓝鲸智云', 'Guest', 'guest', 'admin'])

# 单房间最多连接数
MAX_ROOM_SIZE = int(os.environ.get('MAX_ROOM_SIZE', 3))
# 单进程最多房间数
MAX_ROOM = int(os.environ.get('MAX_ROOM', 2))

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
DEBUG = bool(os.environ.get('DEBUG', False))
WSS = os.environ.get("WSS", "ws")
WSS_MAP = {"https": "wss", "http": "ws"}
HTTP_PROXY = {}

SITE_URL = '/rumpetroll/'
STATIC_URL = '/rumpetroll/'
# 回调URL
DEFAULT_LOG_LEVEL = 'DEBUG'

# 看网络是否需要代理访问API
# HTTP_PROXY = {
#     'proxy_host': '10.192.1.1',
#     'proxy_port': 13128
# }

LOG_FILE = os.environ.get('LOG_FILE', '/tmp/rumpetroll.log')
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

MYSQL_HOSTNAME = os.environ.get("MYSQL_HOSTNAME", '127.0.0.1')
MYSQL_PORT = os.environ.get("MYSQL_PORT", '3306')
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", 'rumpetroll')
MYSQL_USERNAME = os.environ.get("MYSQL_USERNAME", 'root')
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", '')

# 数据连接 URL
DB_URI = f'mysql+pymysql://{MYSQL_USERNAME}:' \
         f'{MYSQL_PASSWORD}@{MYSQL_HOSTNAME}/{MYSQL_DATABASE}?charset=utf8'

POOL = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
RD = redis.Redis(connection_pool=POOL)

ENGINE = create_engine(DB_URI)
BASE = declarative_base(ENGINE)
SESSION = sessionmaker(ENGINE)
SESSION = SESSION()

NAMESPACE_NAME = f'{options.address}:{options.port}'

REGION = make_region().configure(
    'dogpile.cache.redis',
    expiration_time=7200,
    arguments={
        'connection_pool': POOL,
    },
)

# 模板title
TITLE = u"BlueKing"

# 认证模块
AUTH_MODULE = os.environ.get('AUTH_MODULE', 'dummy')

SETTINGS = dict(
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
            'format': f'[%(asctime)s] {NAMESPACE_NAME} %(levelname)s  %(name)s: %(message)s'
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
