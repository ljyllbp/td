import os
import time
import json
import traceback
from sys import exit

def raise_error(error_str, error_record_path=None):
    error_str = str(error_str)
    if error_str.startswith("expect error: "):
        error_str = error_str[14:]
        if error_record_path is not None:
            record_error(error_str, error_record_path)
        print("\nerror:\n")
        print(f"   {error_str}\n")
        exit()
    else:
        record_error(error_str, error_record_path)
        print("\nerror:\n")
        print(f"   未知错误 请联系技术人员检查错误日志\n")
        exit()

def record_error(error_str, error_record_path):
    error_str = str(error_str)
    error_record_root = os.path.dirname(error_record_path)
    if not os.path.exists(error_record_root):
        os.makedirs(error_record_root)
    with open(error_record_path, "a", encoding='utf-8') as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
        f.write("\n")
        f.write(error_str)
        f.write("\n")
        f.write(traceback.format_exc())
        f.write("\n")

def record_json(json_data, json_path):
    json_root = os.path.dirname(json_path)
    if not os.path.exists(json_root):
        os.makedirs(json_root)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def retry_fuction(retry_count, function, *args, **kwargs):
    retry_count += 1
    success_flag = False
    errors = []
    res = None
    while retry_count:
        try:
            res = function(*args, **kwargs)
            success_flag = True
            break
        except Exception as e:
            errors.append(e)
            retry_count -= 1
            continue
    
    return res, errors, success_flag