# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""发送金币消息
"""
import argparse
import json
import logging
import urllib.request as urllib2


LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
LOG = logging.getLogger(__name__)


def _setup_logging(verbose=True):
    if verbose is True:
        level = 'DEBUG'
    else:
        level = 'INFO'
    logging.basicConfig(format=LOG_FORMAT, level=level)


def main(args):
    try:
        url = '{}/rumpetroll/api/gold/?token={}&num={}'.format(args.host, args.token, args.add_golds)
        LOG.debug('REQ: %s', url)
        resp = json.loads(urllib2.urlopen(url).read())
        LOG.debug('RESP: %s', resp)
        if resp.get('result') is True:
            LOG.info(u'添加【%s】个金币成功' % args.add_golds)
        else:
            LOG.info(u'添加金币失败: %s' % resp.get('message', ''))
    except Exception:
        LOG.exception(u"添加金币异常")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=u'发放蝌蚪金币（admin）')
    parser.add_argument('-v', action='store_true', help='verbose mode')
    parser.add_argument('--host', default='http://m.bk.tencent.com', help='rumpetroll host')
    parser.add_argument('--token', default="tPp5GwAmMPIrzXhyyA8X", required=True, help='rumpetroll token')
    parser.add_argument('--add-golds', default=500, metavar='num', type=int, required=True, help=u"添加金币数")

    args = parser.parse_args()
    _setup_logging(args.v)
    main(args)
