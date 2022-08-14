# -*- coding:utf-8 -*-
# @Author : naihai/babydragon


import json
import requests
from bs4 import BeautifulSoup
import os
import time

telephone = "17768100012"
# 进校还是出校
in_or_out = "当日出校再进校"
in_or_out_text = "当日出校且入校 Exit then entry on the day"
# 进出校事由
in_or_out_reason_text = "其他 Others"
in_or_out_reason = "其他"
# 事由描述
description = "实验室在双清大厦，需要前往办公"
# 校外往来地点
destination = "双清大厦4号楼"

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36',
}


class Report(object):
    def __init__(self, user_name_, user_pass_):
        self.user_name = user_name_
        self.user_pass = user_pass_

        self.session = requests.session()
        self.session.headers.update(headers)

        self.server_id = "0ce14db2-d40e-4052-a681-e240fe6c29ee"
        self.resource_id = ""
        self.process_id = ""
        self.user_id = ""
        self.form_id = ""
        self.privilege_id = ""

        self.base_url = "https://thos.tsinghua.edu.cn"

        self.report_url = "https://thos.tsinghua.edu.cn/fp/view?m=fp#from=hall&" \
                          "serveID={0}&" \
                          "act=fp/serveapply".format(self.server_id)

        self.common_referer = "https://thos.tsinghua.edu.cn/fp/view?m=fp"

        self.form_data = None

    def run(self):
        try:
            self.__login()
        except Exception as e:
            print("登录失败", e)
        try:
            self.__get_server_info()
            self.__get_data()
            self.__submit_report()
        except Exception as e:
            print("提交失败", e)

    def __login(self):
        """登录 获取cookie"""

        res1 = self.session.get(self.base_url, headers=headers)  # 重定向到登录页面

        login_url_ = "https://id.tsinghua.edu.cn/do/off/ui/auth/login/check"
        headers_ = headers
        headers_["Referer"] = self.common_referer
        data_ = {
            "i_user": self.user_name,
            "i_pass": self.user_pass,
        }

        res2 = self.session.post(login_url_, data=data_, headers=headers_)
        # 登录成功 会重定向到 在线服务页面
        soup2 = BeautifulSoup(res2.text, 'html.parser')
        redirect_url = soup2.find("a")["href"]
        self.session.get(redirect_url)

        # 验证是否登录成功
        res3 = self.session.get(url=self.report_url, headers=headers)
        soup3 = BeautifulSoup(res3.text, 'html.parser')
        if soup3.find('form', attrs={'class': 'form-signin'}) is not None:
            print("登录失败")
            raise RuntimeError("Login Failed")
        else:
            self.session.headers.update(res3.headers)
            print("登录成功")

    def __get_server_info(self):
        """
        获取服务器提供的一些参数
        resource_id
        formid
        procID
        privilegeId
        """
        check_url = "https://thos.tsinghua.edu.cn/fp/fp/serveapply/checkService"
        headers_ = {}
        # headers_ = self.session.headers
        headers_["Referer"] = self.common_referer
        headers_["Accept"] = 'text/plain, */*; q=0.01'
        headers_["Accept-Encoding"] = 'gzip, deflate, br'
        headers_["accept-language"] = 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        headers_["Cache-Control"] = 'no-cache'
        headers_["Origin"] = 'https://thos.tsinghua.edu.cn'
        headers_["X-Requested-With"] = "XMLHttpRequest"
        headers_["Content-Length"] = '50'
        headers_["content-type"] = 'application/json;charset=UTF-8'
        headers_["pragma"] = 'no-cache'
        headers_["user-agent"] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
        self.session.headers = headers_
        res = self.session.post(url=check_url, data=json.dumps({"serveID": self.server_id}))
        print(res.text)
        url_ = "https://thos.tsinghua.edu.cn/fp/fp/serveapply/getServeApply"

        headers_ = self.session.headers
        headers_["Accept"] = "application/json, text/javascript, */*; q=0.01"
        headers_["Content-Type"] = "application/json"
        headers_["Referer"] = self.common_referer
        headers_["Origin"] = "https://thos.tsinghua.edu.cn"
        headers_["X-Requested-With"] = "XMLHttpRequest"
        headers_["Host"] = "thos.tsinghua.edu.cn"

        data = {"serveID": self.server_id, "from": "hall"}
        try:
            response = self.session.post(url=url_, data=json.dumps(data))
            print(response.status_code)
            result = response.json()

            self.resource_id = result["resource_id"]
            self.user_id = result["user_id"]
            self.form_id = result["formID"]
            self.process_id = result["procID"]
            self.privilege_id = result["privilegeId"]
            print("获取服务器参数成功")
        except Exception as e:
            print("获取服务器参数失败", e)
            raise RuntimeError("Get server info failed")

    def __get_data(self):
        """获取表单信息"""
        url_ = "https://thos.tsinghua.edu.cn/fp/formParser?" \
               "status=select&" \
               "formid={0}&" \
               "service_id={1}&" \
               "process={2}&" \
               "privilegeId={3}".format(self.form_id,
                                        self.server_id,
                                        self.process_id,
                                        self.privilege_id)
        headers_ = self.session.headers
        headers_["Accept"] = "text/html,application/xhtml+xml,application/xml;" \
                             "q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        headers_["Host"] = "thos.tsinghua.edu.cn"
        cookies_ = self.session.cookies

        response = requests.get(url=url_, headers=headers, cookies=cookies_)
        soup = BeautifulSoup(response.text, 'html.parser')

        form_data_str = soup.find("script", attrs={"id": "dcstr"}).extract().text

        self.form_data = eval(form_data_str, type('js', (dict,), dict(__getitem__=lambda k, n: n))())

    def __submit_report(self):
        obj_keys = self.form_data["body"]["dataStores"]
        for key in obj_keys:
            if '-' in key:
                key_val = key
                break
        student_id = self.form_data["body"]["dataStores"]["variable"]["rowSet"]["primary"][8]["value"]
        name = self.form_data["body"]["dataStores"]["variable"]["rowSet"]["primary"][9]["value"]
        department = self.form_data["body"]["dataStores"]["variable"]["rowSet"]["primary"][10]["value"]
        unit_id = self.form_data["body"]["dataStores"]["variable"]["rowSet"]["primary"][11]["value"]
        student_type = self.form_data["body"]["dataStores"]["variable"]["rowSet"]["primary"][12]["value"]
        self.form_data["body"]["dataStores"][key_val]["rowSet"]["primary"].append({
            "XH": student_id,
            # "_t": 3,
            "XM": "田宝林",
            "SZYX": "软件学院",
            "BJ": "",
            "YXDM": unit_id,
            "XSLX": "硕士研究生",
            "LXDH": telephone,
            "JCX_TEXT": in_or_out_text,
            "JCX": in_or_out,
            "YY_TEXT": in_or_out_reason_text,
            "YY": in_or_out_reason,
            "CXSY": description,
            "NQWDD": destination,
            "SQHXRQQS": time.strftime("%Y-%m-%d", time.localtime()),
            "ZJSFMQT_TEXT": "是 Yes",
            "ZJSFMQT": "是",
            "NJXSJ_TEXT": "22:00", "NJXSJ": "22:00", "NCXSJ_TEXT": "10:00", "NCXSJ": "10:00", "ZJZX_TEXT": "请选择",
            "ZJZX": "", "SFQJ_TEXT": "请选择", "SFQJ": "", "DSSFTY_TEXT": "请选择", "DSSFTY": "",
            "BZ": "",
            "_o": {
                "XH": None,
                "XM": None,
                "SZYX": None,
                "BJ": None,
                "YXDM": None,
                "XSLX": None,
                "LXDH": None,
                "JCX_TEXT": None,
                "JCX": None,
                "YY_TEXT": None,
                "YY": None,
                "CXSY": None,
                "NQWDD": None,
                "SQHXRQQS": None,
                "BZ": None
            }
        })
        url_ = "https://thos.tsinghua.edu.cn/fp/formParser?" \
               "status=update&" \
               "formid={0}&" \
               "workflowAction=startProcess&" \
               "seqId=&unitId=&applyCode=&workitemid=&" \
               "process={1}".format(self.form_id,
                                    self.process_id)

        referer_url_ = "https://thos.tsinghua.edu.cn/fp/formParser?" \
                       "status=select&" \
                       "formid={0}&" \
                       "service_id={1}&" \
                       "process={2}&" \
                       "privilegeId={3}".format(self.form_id,
                                                self.server_id,
                                                self.process_id,
                                                self.privilege_id)

        self.form_data["body"]["dataStores"]["uploader_1"] = \
            {"rowSet":{"primary":[{"div_name":"上传北京健康宝","div_id":"uploader_1","up_id":"fileupload_KKD08AP68H43REQ88ISQI3NVA","file_size":"56026","up_relative_path":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/8/14/","up_file_new_name":"e8e18088873f486494006105efb0.jpg","up_newurl":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/8/14/e8e18088873f486494006105efb0.jpg","up_encodeName":"avator1.jpg","_t":1}],"filter":[],"delete":[]},"name":"uploader_1", "pageNumber" :1, "pageSize" : 2147483647, "recordCount":0,"parameters":{"uploader":"true","exist":"true"}}
        self.form_data["body"]["dataStores"]["uploader_2"] = \
            {"rowSet":{"primary":[{"div_name":"上传通信行程码","div_id":"uploader_2","up_id":"fileupload_4E3BPTBBHHQ7HIQ3IK60SQ71Q","file_size":"29602","up_relative_path":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/8/14/","up_file_new_name":"3582171d22724e368b650443c3d2.jpg","up_newurl":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/8/14/3582171d22724e368b650443c3d2.jpg","up_encodeName":"avator.jpg","_t":1}],"filter":[],"delete":[]},"name":"uploader_2","pageNumber":1,"pageSize":2147483647,"recordCount":0,"parameters":{"uploader":"true","exist":"true"}}
        self.form_data["body"]["dataStores"]["uploader_3"] = \
            {"rowSet":{"primary":[{"div_name":"上传个人承诺书","div_id":"uploader_3","up_id":"fileupload_884EK7N66QDQ8F871SSFFGIO1","file_size":"449454","up_relative_path":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/6/28/","up_file_new_name":"24c5f20077e54201901b5b431c2f.jpg","up_newurl":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/6/28/24c5f20077e54201901b5b431c2f.jpg","up_encodeName":"Screenshot_2022-06-26-21-24-05-012_com.tencent.mm.jpg","_t":1}],"filter":[],"delete":[]},"name":"uploader_3","pageNumber":1,"pageSize":2147483647,"recordCount":0,"parameters":{"uploader":"true","exist":"true"}}
        self.form_data["body"]["dataStores"]["uploader_0"] = {"rowSet":{"primary":[{"_t":1}],"filter":[],"delete":[]},"name":"uploader_0","pageNumber":1,"pageSize":2147483647,"recordCount":0,"parameters":{"uploader":"true","exist":"true"}}
        self.form_data["body"]["dataStores"]["uploader_4"] = {"rowSet":{"primary":[{"div_name":"上传核酸","div_id":"uploader_4","up_id":"fileupload_DGM5LQKPNDMJOBDCR35IUVIV1","file_size":"477056","up_relative_path":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/6/28/","up_file_new_name":"7d07e36af3594cf0a1cdc5178052.jpg","up_newurl":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/6/28/7d07e36af3594cf0a1cdc5178052.jpg","up_encodeName":"Screenshot_2022-06-28-23-09-29-249_com.tencent.mm.jpg","_t":1},{"div_name":"上传核酸","div_id":"uploader_4","up_id":"fileupload_HKDMOAO06BVGV401N9V7QGA62","file_size":"475550","up_relative_path":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/7/1/","up_file_new_name":"5b91eecfd5f040aba2a66d0d6a26.jpg","up_newurl":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/7/1/5b91eecfd5f040aba2a66d0d6a26.jpg","up_encodeName":"Screenshot_2022-07-01-08-28-44-042_com.tencent.mm.jpg","_t":1},{"div_name":"上传核酸","div_id":"uploader_4","up_id":"fileupload_P57NSQ63IUNII5PIAGUQENPIO","file_size":"491666","up_relative_path":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/7/4/","up_file_new_name":"7ef25ce597844cdca010cb21b1d8.jpg","up_newurl":"uploadfiles/serviceUpload/0ce14db2-d40e-4052-a681-e240fe6c29ee/2022/7/4/7ef25ce597844cdca010cb21b1d8.jpg","up_encodeName":"Screenshot_2022-07-04-19-21-24-347_com.tencent.mm.jpg","_t":1}],"filter":[],"delete":[]},"name":"uploader_4","pageNumber":1,"pageSize":2147483647,"recordCount":0,"parameters":{"uploader":"true","exist":"true"}}
        headers_ = self.session.headers
        self.form_data["body"]["dataStores"]["variable"] = {
            "rowSet": {
                "primary": [
                    {
                        "name": "学生类型",
                        "source": "process",
                        "type": "string",
                        "value": "硕士研究生",
                        "_t": 1,
                        "_o": {
                            "value": ""
                        }
                    },
                    {
                        "name": "BUSINESS_UNIT",
                        "source": "process",
                        "type": "string",
                        "value": ""
                    },
                    {
                        "name": "进出校类型",
                        "source": "process",
                        "type": "string",
                        "value": "其他 Others",
                        "_t": 1,
                        "_o": {
                            "value": ""
                        }
                    },
                    {
                        "name": "班级",
                        "source": "process",
                        "type": "string",
                        "value": "201",
                        "_t": 1,
                        "_o": {
                            "value": ""
                        }
                    },
                    {
                        "name": "是否冬奥志愿者",
                        "source": "process",
                        "type": "string",
                        "value": "0",
                        "_t": 1,
                        "_o": {
                            "value": ""
                        }
                    },
                    {
                        "name": "学号",
                        "source": "process",
                        "type": "string",
                        "value": "2020214026",
                        "_t": 1,
                        "_o": {
                            "value": ""
                        }
                    },
                    {
                        "name": "进出校",
                        "source": "process",
                        "type": "string",
                        "value": "当日出校再进校",
                        "_t": 1,
                        "_o": {
                            "value": ""
                        }
                    },
                    {
                        "name": "SYS_USER",
                        "source": "interface",
                        "type": "string",
                        "value": "田宝林"
                    },
                    {
                        "name": "SYS_UNIT",
                        "source": "interface",
                        "type": "string",
                        "value": "软件学院 "
                    },
                    {
                        "name": "SYS_DATE",
                        "source": "interface",
                        "type": "date",
                        "value": "1660466743207"
                    },
                    {
                        "name": "716e67c5-a4ae-4d51-95b8-92c4a9c5.ID_NUMBER",
                        "value": "2020214026"
                    },
                    {
                        "name": "716e67c5-a4ae-4d51-95b8-92c4a9c5.USER_NAME",
                        "value": "田宝林"
                    },
                    {
                        "name": "716e67c5-a4ae-4d51-95b8-92c4a9c5.UNIT_NAME",
                        "value": "软件学院"
                    },
                    {
                        "name": "716e67c5-a4ae-4d51-95b8-92c4a9c5.UNIT_ID",
                        "value": "410"
                    },
                    {
                        "name": "716e67c5-a4ae-4d51-95b8-92c4a9c5.YHLB",
                        "value": "硕士研究生"
                    },
                    {
                        "name": "503992773193728.CNT",
                        "value": "0"
                    }
                ],
                "filter": [],
                "delete": []
            },
            "name": "variable",
            "pageNumber": 1,
            "pageSize": 2147483647,
            "recordCount": 0,
            "parameters": {}
        }
        headers_["Origin"] = "https://thos.tsinghua.edu.cn"
        headers_["Host"] = "thos.tsinghua.edu.cn"
        headers_["Sec-Fetch-Mode"] = "cors"
        headers_["Sec-Fetch-Site"] = "same-origin"
        headers_["Referer"] = referer_url_

        response = self.session.post(url_, data=json.dumps(self.form_data), headers=headers_)
        if response.status_code == requests.codes.OK:
            print("提交申请出校成功")
            print(response.text)
        else:
            print("提交申请出校失败")


def load_info():
    with open("conf.ini") as rf:
        line = rf.readlines()
        user_name_ = line[0].strip().split("=")[1].strip()
        user_pass_ = line[1].strip().split("=")[1].strip()
    return user_name_, user_pass_


if __name__ == '__main__':
    # 首先检查环境变量中是否存在 USER_NAME USER_PASS
    # 该功能用于Github Action部署
    if os.getenv("USER_NAME") and os.getenv("USER_PASS"):
        print("User info found in env")
        user_name = os.getenv("USER_NAME")
        user_pass = os.getenv("USER_PASS")
        telephone = os.getenv("USER_TELEPHONE")
    else:
        user_name, user_pass = load_info()
    Report(user_name, user_pass).run()
