# -*- coding: utf-8 -*-
# Copyright 2016 Tencent
# Author: 蓝鲸智云
import xlwt


def export2excel(data_list, head_list, string_io):
    """导出到excel统一处理方法"""
    # 设置表格文件格式
    wbk = xlwt.Workbook(encoding='utf-8')
    sheet = wbk.add_sheet('sheet1')
    # 设置字体
    fnt = xlwt.Font()
    fnt.name = u"宋体"
    fnt.height = 220  # 字体大小
    fnt.bold = False  # 设置非粗体
    style = xlwt.easyxf('align: wrap on, vert centre, horiz centre;')  # 设置字体自动换行，垂直水平居中
    style.font = fnt
    for i, head in enumerate(head_list):
        sheet.col(i).width = 7000  # 设置宽度
        sheet.write(0, i, head[1], style)  # 添加头

    for row, data in enumerate(data_list, start=1):  # row需要从1开始
        for col, head in enumerate(head_list):  # col从0开始
            sheet.write(row, col, data.get(head[0], '--'), style)

    # 返回一个response
    # now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # name = name.encode('utf-8')  # django HTTP response headers must be in US-ASCII format
    # response = HttpResponse(mimetype="application/ms-excel")
    # response['Content-Disposition'] = "attachment; filename=%s-%s.xls" % (name, now)
    # wbk.save(response)
    wbk.save(string_io)
    return string_io
