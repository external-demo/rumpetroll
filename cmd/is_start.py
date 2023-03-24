"""
# Copyright 2017 Tencent
# Author: 蓝鲸智云
"""
from common.utils_func import get_func_control, set_func_control
import os.path
import sys


def main():
    os.environ['HOST'] = 'm.bkclouds.cc'
    os.environ['RUN_MODE'] = 'PROD'

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

    FUNC_CODE = 'is_start'
    is_enabled = True
    names = {
        'admin': 'ov6bLjuj0pJfj_dENx7sLWZpEcrg',
        'hahayang': 'ov6bLji5yqx0GAVL-9BN7PjSK4JA',
    }

    print(set_func_control(FUNC_CODE, is_enabled, names.values()))
    print(get_func_control(FUNC_CODE))


if __name__ == '__main__':
    main()
