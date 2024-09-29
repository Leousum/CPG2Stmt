import os
import json
import time

class LogManager():
    def __init__(self) -> None:
        self.log_root = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "logs", time.strftime("%Y-%m-%d", time.localtime()))
        if not os.path.exists(self.log_root):
            os.makedirs(self.log_root, mode = 0o777)
        self.log_path = os.path.join(self.log_root, f"log.txt")
        self.json_path = os.path.join(self.log_root, f"logs.json")
        self.log_info(f'Start record log information!', True, 0)

    def log_info(self, log_content: str, is_title = False, indent_num = 0):
        '''记录日志信息'''
        log_content = f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] {log_content}'
        if is_title:
            log_content = "===================================" + log_content
        else:
            log_content = "|-" + log_content
        for i in range(indent_num):
            log_content = "    " + log_content
        if is_title:
            log_content = log_content + "==================================="
        print(log_content)
        with open(self.log_path, "a", encoding = "utf-8") as log_file:
            print(f'{log_content}', file = log_file)
    
    def log_result(self, json_key: str, json_content):
        '''记录中间结果'''
        data = dict()
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding = "utf-8") as log_file:
                data = json.load(log_file)
        data[json_key] = json_content
        with open(self.json_path, "w", encoding = "utf-8") as log_file:
            json.dump(data, log_file, ensure_ascii = False, indent = 4)
    
    def get_log_result(self, json_key: str):
        '''获取日志信息'''
        data = dict()
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding = "utf-8") as log_file:
                data = json.load(log_file)
        if json_key in data.keys():
            return data[json_key]
        return None