#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/9 15:17
# @Author  : lixiaofeng
# @Site    :
# @File    : swagger.py
# @Software: PyCharm


import os, requests
from lib.processingJson import write_data, get_json


class AnalysisJson:
    """swagger自动生成测试用例"""

    def __init__(self, url):
        self.url = url
        self.interface = {}
        self.case_list = []
        self.tags_list = []
        self.http_suite = {"config": {"name": "", "base_url": "", "variables": {}},
                           "testcases": []}
        self.http_testcase = {"name": "", "testcase": "", "variables": {}}

    def retrieve_data(self):
        """
        主函数
        :return:
        """
        try:
            r = requests.get('https://generator.swagger.io/api/swagger.json').json()
            write_data(r, 'data.json')
            # r = get_json('D:\HttpRunner_framework\\testcases\data.json')
        except Exception as e:
            # logger.log_error('请求swagger url 发生错误. 详情原因: {}'.format(e))
            print('请求swagger url 发生错误. 详情原因: {}'.format(e))
            return 'error'
        self.data = r['paths']  # 接口数据
        self.url = 'https://' + r['host']
        self.title = r['info']['title']
        self.http_suite['config']['name'] = self.title
        self.http_suite['config']['base_url'] = self.url

        self.definitions = r['definitions']  # body参数
        for tag_dict in r['tags']:
            self.tags_list.append(tag_dict['name'])
        i = 0
        for tag in self.tags_list:
            self.http_suite['testcases'].append({"name": "", "testcase": "", "variables": {}})
            self.http_suite['testcases'][i]['name'] = tag
            self.http_suite['testcases'][i]['testcase'] = 'testcases/' + tag + '.json'
            i += 1

        suite_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname("__file__"), os.path.pardir)),
                                  'testsuites')
        testcase_path = os.path.join(suite_path, 'demo_testsuite.json')
        write_data(self.http_suite, testcase_path)
        if isinstance(self.data, dict):
            for tag in self.tags_list:
                self.http_case = {"config": {"name": "", "base_url": "", "variables": {}}, "teststeps": []}

                for key, value in self.data.items():
                    for method in list(value.keys()):
                        params = value[method]
                        if not params['deprecated']:  # 接口是否被弃用
                            if params['tags'][0] == tag:
                                self.http_case['config']['name'] = params['tags'][0]
                                self.http_case['config']['base_url'] = self.url
                                case = self.retrieve_params(params, key, method, tag)
                                self.http_case['teststeps'].append(case)
                        else:
                            # logger.log_info(
                            #     'interface path: {}, if name: {}, is deprecated.'.format(key, params['description']))
                            break
                api_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname("__file__"), os.path.pardir)),
                                        'testcases')
                testcase_path = os.path.join(api_path, tag + '.json')
                write_data(self.http_case, testcase_path)


        else:
            # logger.log_error('解析接口数据异常！url 返回值 paths 中不是字典.')
            print('解析接口数据异常！url 返回值 paths 中不是字典.')
            return 'error'

    def retrieve_params(self, params, api, method, tag):
        """
        解析json，把每个接口数据都加入到一个字典中
        :param params:
        :param params_key:
        :param method:
        :param key:
        :return:
        replace('false', 'False').replace('true', 'True').replace('null','None')
        """
        http_interface = {"name": "", "variables": {},
                          "request": {"url": "", "method": "", "headers": {}, "json": {}, "params": {}}, "validate": [],
                          "output": []}
        http_testcase = {"name": "", "api": "", "variables": {}, "validate": [], "extract": [], "output": []}

        name = params['summary'].replace('/', '_')
        http_interface['name'] = name
        http_testcase['name'] = name
        http_testcase['api'] = 'api/{}/{}.json'.format(tag, name)
        http_interface['request']['method'] = method.upper()
        http_interface['request']['url'] = api.replace('{', '$').replace('}', '')
        parameters = params.get('parameters')  # 未解析的参数字典
        responses = params.get('responses')
        if not parameters:  # 确保参数字典存在
            parameters = {}
        for each in parameters:
            if each.get('in') == 'body':  # body 和 query 不会同时出现
                schema = each.get('schema')
                if schema:
                    ref = schema.get('$ref')
                    if ref:
                        param_key = ref.split('/')[-1]
                        param = self.definitions[param_key]['properties']
                        for key, value in param.items():
                            if 'example' in value.keys():
                                http_interface['request']['json'].update({key: value['example']})
                            else:
                                http_interface['request']['json'].update({key: ''})
            elif each.get('in') == 'query':
                name = each.get('name')
                for key in each.keys():
                    if 'example' in key:
                        http_interface['request']['params'].update({name: each[key]})
        for each in parameters:
            # if each.get('in') == 'path':
            #     name = each.get('name')
            #     for key in each.keys():
            #         if 'example' in key:
            #             http_interface['request']['json'].update({name: each[key]})
            #     else:
            #
            #         http_interface['request']['json'].update({name: ''})
            if each.get('in') == 'header':
                name = each.get('name')
                for key in each.keys():
                    if 'example' in key:
                        http_interface['request']['headers'].update({name: each[key]})
                    else:
                        if name == 'token':
                            http_interface['request']['headers'].update({name: '$token'})
                        else:
                            http_interface['request']['headers'].update({name: ''})
        for key, value in responses.items():
            schema = value.get('schema')
            if schema:
                ref = schema.get('$ref')
                if ref:
                    param_key = ref.split('/')[-1]
                    res = self.definitions[param_key]['properties']
                    i = 0
                    for k, v in res.items():
                        if 'example' in v.keys():
                            http_interface['validate'].append({"eq": []})
                            http_interface['validate'][i]['eq'].append('content.' + k)
                            http_interface['validate'][i]['eq'].append(v['example'])

                            http_testcase['validate'].append({"eq": []})
                            http_testcase['validate'][i]['eq'].append('content.' + k)
                            http_testcase['validate'][i]['eq'].append(v['example'])
                            i += 1
                else:
                    http_interface['validate'].append({"eq": []})
            else:
                http_interface['validate'].append({"eq": []})
        if http_interface['request']['json'] == {}:
            del http_interface['request']['json']
        if http_interface['request']['params'] == {}:
            del http_interface['request']['params']

        api_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname("__file__"), os.path.pardir)), 'api')
        tags_path = os.path.join(api_path, tag)
        if not os.path.exists(tags_path):
            os.mkdir(tags_path)
        json_path = os.path.join(tags_path, http_interface['name'] + '.json')
        write_data(http_interface, json_path)

        return http_testcase


if __name__ == '__main__':
    AnalysisJson('1').retrieve_data()