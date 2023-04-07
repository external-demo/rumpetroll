# -*- coding: utf-8 -*-
"""
校验提交模型字段是否符合规范
"""
# pylint: disable=broad-except
from __future__ import absolute_import, print_function, unicode_literals

import argparse
import csv
import hashlib
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 尝试重新载入 sys 模块
try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except NameError:
    # 如果发生 NameError 异常，则表示运行在 python3 环境下
    # 在 python3 中，这些字符已经默认使用 unicode 编码了，因此不需要设置编码
    pass


def read_csv():
    csv_path = os.path.join(BASE_DIR, 'field_library.csv')
    csv_file = csv.reader(open(csv_path, 'r'))
    i = 1
    ret_json = {}
    for line in csv_file:
        if i == 1:
            i += 1
            continue
        correct_field, error_fields = line[0], line[2].split(',')
        for field in error_fields:
            if field:
                ret_json[field] = correct_field
    return ret_json


# 定义一个保存函数，参数为 content
def save(content):
    # 检查参数是否存在
    if content:
        # json 文件路径
        json_path = os.path.join(BASE_DIR, 'field_library.json')
        # 打开 json 文件，并以写入模式写入内容
        with open(json_path, 'w') as fp:
            # 将 content 内容以 JSON 格式存储到文件中
            json.dump(content, fp)



def get_field_library():
    json_path = os.path.join(BASE_DIR, 'field_library.json')
    if not os.path.exists(json_path):
        field_library = read_csv()
        save(field_library)
    with open(json_path, 'r') as fp:
        content = json.load(fp)
        return content


def get_str_md5(content):
    md5hash = hashlib.md5(content.encode("utf8"))
    md5 = md5hash.hexdigest()
    return md5


def handle_rename_model(file_path, library):
    rename_content = {}
    with open(file_path, 'r') as fp:
        ret = fp.readlines()
        rename = False
        index = 0
        for line in ret:
            single_line = line.strip().strip(',')
            if 'RenameField(' in single_line:
                index += 1
                rename_content[index] = {}
                rename = True
                continue
            if rename:
                if single_line.startswith('model_name='):
                    model_name = single_line.split('=')[1]
                    rename_content[index]['model_name'] = eval(model_name)
                    continue
                if single_line.startswith('old_name='):
                    field_name = single_line.split('=')[1]
                    rename_content[index]['old_name'] = eval(field_name)
                    continue
                if single_line.startswith('new_name='):
                    field_name = single_line.split('=')[1]
                    rename_content[index]['new_name'] = eval(field_name)
                    rename = False
                    continue
    err_list = []
    for _, value in rename_content.items():
        suggested_naming = library.get(value['new_name'])
        if suggested_naming:
            err_list.append(
                'Field ({}) in Model ({}) might be replaced by ({})'.format(
                    value['new_name'], value['model_name'], suggested_naming
                )
            )
    return err_list


def handle_add_alter_model(file_path, library):
    add_alter_content = {}
    with open(file_path, 'r') as fp:
        ret = fp.readlines()
        alter = False
        index = 0
        for line in ret:
            single_line = line.strip().strip(',')
            if 'AddField(' in single_line or 'AlterField(' in single_line:
                index += 1
                add_alter_content[index] = {}
                alter = True
                continue
            if alter:
                if single_line.startswith('model_name='):
                    model_name = single_line.split('=')[1]
                    add_alter_content[index]['model_name'] = eval(model_name)
                    continue
                if single_line.startswith('name='):
                    field_name = single_line.split('=')[1]
                    add_alter_content[index]['name'] = eval(field_name)
                    alter = False
                    continue
    err_list = []
    for _, value in add_alter_content.items():
        suggested_naming = library.get(value['name'])
        if suggested_naming:
            err_list.append(
                'Field ({}) in Model ({}) might be replaced by ({})'.format(
                    value['name'], value['model_name'], suggested_naming
                )
            )
    return err_list


def handle_create_model(file_path, library):
    create_content = {}
    with open(file_path, 'r') as fp:
        ret = fp.readlines()
        create = False
        index = 0
        for line in ret:
            single_line = line.strip().strip(',')
            if 'CreateModel(' in single_line:
                create = True
                index += 1
                create_content[index] = []
                continue
            if create:
                if single_line.startswith('name='):
                    create_content[index].append(single_line)
                    continue
                if 'fields' in single_line:
                    single_line = single_line.replace('fields=[', '')
                    if single_line:
                        create_content[index].append(single_line)
                    continue
                if single_line.endswith(']'):
                    create = False
                    continue
                if single_line.startswith('(') and 'Field' in single_line:
                    create_content[index].append(single_line)
    fields_dict = {}
    for _, values in create_content.items():
        model_name = eval(values[0].split('=')[1])
        fields_dict[model_name] = []
        for value in values[1:]:
            in_value = value.rstrip(')').lstrip('(')
            param = in_value.split(',', 1)[0]
            fields_dict[model_name].append(eval(param))
    err_list = []
    for model_name, fields in fields_dict.items():
        for field in fields:
            suggested_naming = library.get(field)
            if suggested_naming:
                err_list.append(
                    'Field ({}) in Model ({}) might be replaced by ({})'.format(field, model_name, suggested_naming)
                )
    return err_list


def get_new_field(result):
    exist_field = []
    if 'field_error_detail.log' in os.listdir('.'):
        with open('field_error_detail.log', 'r') as fp:
            exist_field = eval(fp.read())
    new_field = []
    for line in result:
        if get_str_md5(line) not in exist_field:
            print(line)
            new_field.append(get_str_md5(line))
    with open('field_error_detail.log', 'w') as fp:
        fp.write(str(exist_field + new_field))
    return new_field


# 定义函数 main，接收参数 argv，默认为 None
def main(argv=None):
    try:
        # 创建 ArgumentParser 对象
        parser = argparse.ArgumentParser()
        # 向 ArgumentParser 添加命令行参数 'filenames'（可传入多个文件名）
        parser.add_argument('filenames', nargs='*')
        # 解析命令行参数，返回一个 Namespace 类型实例的对象到 args 中
        args = parser.parse_args(argv)
        # 获取当前数据库中已有的所有字段信息
        field_library = get_field_library()
        # 存放处理结果的列表
        result = []
        # 遍历所用到的文件名
        for file_path in args.filenames:
            # 更改目录分隔符为系统默认，并将路径拆分成各级目录列表
            directory = file_path.split(os.sep)
            # 如果目录层数大于1
            if len(directory) > 1:
                # 判断最后两级目录是否为'migrations'和以'.py'结尾
                if directory[-2] == 'migrations' and directory[-1].endswith('.py'):
                    # 取得文件所在项目的根目录
                    base_dir = os.path.dirname(os.path.dirname(BASE_DIR))
                    # 组成完整的文件路径
                    full_path = os.path.join(base_dir, file_path)
                    # 处理该文件的 create_model，并记录异常信息
                    create_err_field = handle_create_model(full_path, field_library)
                    # 处理该文件的 add/alter model，并记录异常信息
                    alter_err_field = handle_add_alter_model(full_path, field_library)
                    # 处理该文件的 rename model，并记录异常信息
                    rename_err_field = handle_rename_model(full_path, field_library)
                    # 将所有异常信息添加到结果列表中，格式为 'File 文件名: 异常信息'
                    for err in create_err_field + alter_err_field + rename_err_field:
                        result.append('File {}: {}'.format(directory[-1], err))
        # 如果处理结果列表不为空
        if result:
            # 获取所有新建字段的信息
            new_field = get_new_field(result)
            # 如果有新建字段，打印提示语并返回 1
            if new_field:
                print('Some field not standard, please check.')
                print('if you still want to commit, try it again')
                return 1
        # 处理完成，返回0
        return 0
    # 捕获任何异常，并输出提示语句，并返回 0
    except Exception:
        print('Unexpected exception occurred')
        return 0



if __name__ == '__main__':
    exit(main())
