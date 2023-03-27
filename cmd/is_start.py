"""
# Copyright 2017 Tencent
# Author: 蓝鲸智云
"""
import os.path
import sys

from common.utils_func import get_func_control, set_func_control


def main():
    os.environ['HOST'] = 'm.bkclouds.cc'
    os.environ['RUN_MODE'] = 'PROD'

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if base_dir not in sys.path:
        sys.path.append(base_dir)

    func_code = 'is_start'
    is_enabled = True
    names = {
        'admin': 'ov6bLjuj0pJfj_dENx7sLWZpEcrg',
        'hahayang': 'ov6bLji5yqx0GAVL-9BN7PjSK4JA',
    }

    print(set_func_control(func_code, is_enabled, names.values()))
    print(get_func_control(func_code))


if __name__ == '__main__':
    main()
