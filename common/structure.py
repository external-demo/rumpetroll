"""
# Copyright 2016 Tencent
# Author: 蓝鲸智云
"""
import json


class SyncPosition(object):
    """
    sync position
    """

    def __init__(self, gson=""):
        self.__dict__ = json.loads(gson)


class SyncData(object):
    """
    sync data
    """

    def __init__(self):
        self.type = "message"
        self.message = ""


class InitData(object):
    """
    init data
    """

    def __init__(self, id):
        self.type = "welcome"
        self.id = id


class CloseData(object):
    """
    close data
    """

    def __init__(self, id):
        self.type = "closed"
        self.id = id  # noqa
