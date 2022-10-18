# -*- coding: utf-8 -*-
# Copyright 2017 Tencent
# Author: Joe Lei <joelei@tencent.com>
import settings

if settings.AUTH_MODULE == 'enterprise':
    from auth.enterprise import *  # noqa
elif settings.AUTH_MODULE == 'mp':
    from auth.mp import *  # noqa
elif settings.AUTH_MODULE == 'mp_tencent':
    from auth.mp_tencent import *  # noqa
else:
    from auth.dummy import *  # noqa
