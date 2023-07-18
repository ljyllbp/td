import os
import hashlib
from PIL import Image
from PIL import ImageFile
import time
import requests
import threading
import uuid
import json
import shutil
from utils.pulic_tool import raise_error, retry_fuction, record_error, record_json
import time
from pathlib import Path

from config import *
from utils import oss, executor

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


class upload(object):
    def __init__(self, ds_id, data_root):
        self.data_root = self.as_posix(Path(data_root).absolute())
        
        time_str = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()).replace(" ", "_").replace(":","-")
        pre =  os.path.expanduser('~') + f"/.td/upload/{time_str}/" + os.path.basename(data_root)

        self.error_record_path = f"{pre}/error.txt"
        self.add_files_record_path = f"{pre}/add_file_record.json"

        self.batch_sn_request_record_path = f"{pre}/batch_sn_request_record.json"
        self.batch_sn_request_res_path = f"{pre}/batch_sn_request_res.json"

        self.oss_config_request_record_path = f"{pre}/oss_config_request_record.json"
        self.oss_config_request_res_path = f"{pre}/oss_config_request_res.json"

        self.file_list_pre_upload_record_path = f"{pre}/file_list_pre_upload_record.json"
        self.file_list_pre_upload_res_path = f"{pre}/file_list_pre_upload_res.json"

        self.call_back_fail_record_path = f"{pre}/call_back_fail_record.json"
        self.call_back_success_record_path = f"{pre}/call_back_success_record.json"

        self.id_request_record_path = f"{pre}/id_request_record.json"
        self.id_request_res_path = f"{pre}/id_request_res.json"

        self.upload_cache_root = self.get_upload_cache_root()
        self.use_cache = True
        if not os.path.exists(self.upload_cache_root):
            self.use_cache = False
        self.save_cache = True

        self.log_path = f"{pre}/log"
        self.log_fp = self.get_log_fp()

        

        self.debug = False
        self.upload_files_path = {}
        self.add_files_path = []
        self.add_file_name = ".add_record.json"
        self.move_files = {}

        self.package_count = None

        self.is_simplify_pcd = False
        self.is_force_Compressed = False

        self.ds_id = ds_id
        self.host = None
        self.ak = None
        self.batch_sn = None
        self.oss_config = None
        self.callback_url = None
        self.error_callback_url = None
        self.id = None
        self.process_type = None

        self.oss_class = None

        self.uploaded_files_count = 0  # 已经上传的文件数量
        self.upload_files_count = 0  # 需要上传的文件数量
        self.success_uploaded_files_count = 0  # 成功上传的数量
        self.fail_uploaded_files_count = 0  # 失败上传的数量

        self.executor = executor.Executor()  # 多线程
        self.executor_functions = []
        self.lock = threading.Lock()
        self.retry_count = 10  # 尝试次数

    def set_debug(self, debug):
        self.debug = debug

    def set_retry_count(self, retry_count):
        self.retry_count = retry_count

    def set_host_and_ak(self, host, ak):
        self.host = host
        self.ak = ak
    
    def set_package_count(self, package_count):
        self.package_count = package_count

    def set_executor(self, thread_num):
        self.executor = executor.Executor(thread_num)
    
    def set_pcd_option(self, is_simplify_pcd, is_force_Compressed):
        self.is_simplify_pcd = is_simplify_pcd
        self.is_force_Compressed = is_force_Compressed
    
    def set_batch_sn(self, batch_sn):
        self.batch_sn = batch_sn
    
    def set_use_cache(self, no_cache):
        self.use_cache = not no_cache
        if not os.path.exists(self.upload_cache_root):
            self.use_cache = False
    
    def save_add_files(self):
        add_files_record_root = os.path.dirname(self.add_files_record_path)
        if not os.path.exists(add_files_record_root):
            os.makedirs(add_files_record_root)
        with open(self.add_files_record_path, "w", encoding="utf-8") as f:
            json.dump(self.add_files_path, f, ensure_ascii=False, indent=4)
    
    def as_posix(self, file_path):
        return Path(file_path).as_posix()

    def path_join(self, *args):
        return self.as_posix(os.path.join(*args))

    @staticmethod
    def get_data_type(host, ds_id, ak):
        try:
            url_ds_info = f"{host}/v2/datasets/{ds_id}"
            headers = {"Access-Key": ak, "User-Agent": "apifox/1.0.0"}
            r = requests.get(url_ds_info, headers=headers)
            assert r.status_code == 200
            res = r.json()
            return res["data"]["data_type"]
        except Exception as e:
            error_str = f"expect error: 获取数据集类型失败，请检查 host:{host}，数据集id:{ds_id}，密钥:{ak}"
            raise_error(error_str)
    
    def get_upload_cache_root(self):
        buffer = self.data_root.encode("utf-8")
        data_root_md5 = hashlib.md5(buffer).hexdigest()
        return os.path.expanduser('~') + f"/.td/upload_cache/{data_root_md5}"

    def assert_illegal_characters(self, path):
        for character in ILLEGAL_CHARACTER:
            if character in path:
                raise Exception(f"expect error: {path} 路径中不允许出现特殊字符'{character}'")
        try:
            path.encode("utf-8")
        except:
            raise Exception(f"expect error: {path} 请使用符合规范的UTF-8字符")

    def get_id_prelabel(self, id_index, ids):
        while True:
            id = "yspre-" +  str(id_index).rjust(6,"0")
            if id in ids:
                id_index += 1
                if id_index >= 1000000:
                    raise Exception(f"获取id失败")
                continue
            return id, id_index
    
    def assert_id(self, id):
        legal_words = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '_']
        if not isinstance(id, str):
            raise Exception(f"id 类型错误,应为字符串")
        if len(id) > 32:
            raise Exception(f"id 长度不能超过32")
        if len(id) == 0:
            raise Exception(f"id 不能为空")
        for word in id:
            if word not in legal_words:
                raise Exception(f"非法字符:{word}, 应为大小写字母,数字,'-','_'")
        
    def delete_add_files(self):
        if os.path.exists(self.add_files_record_path):
            with open(self.add_files_record_path, "r", encoding="utf-8") as f:
                add_files_path = json.load(f)
                for add_file_path in add_files_path:
                    if os.path.exists(add_file_path):
                        if os.path.isfile(add_file_path):
                            os.remove(add_file_path)
                        else:
                            shutil.rmtree(add_file_path)
            os.remove(self.add_files_record_path)

    def get_upload_class(self):
        oss_type = self.oss_config["oss_type"]
        if oss_type == "ali_oss":
            self.oss_class = oss.AliyunClass()
        elif oss_type == "minio":
            self.oss_class = oss.MinioClass()
        else:
            raise Exception(f"expect error: 暂不支持{oss_type}类型对象存储")

    def get_log_fp(self):
        self.make_dir(self.log_path)
        log_fp = open(self.log_path, "a", encoding="utf-8")
        log_fp.write("-----------------TESTIN TD LOG-----------------\n")
        log_fp.write(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
        log_fp.write("\n")
        return log_fp
    
    def loged(self, str_, end = None):
        if end is None:
            self.log_fp.write(str(str_) + "\n")
        else:
            self.log_fp.write(str(str_) + end)
        if self.debug:
            print(str_, end=end)
    
    def close_log_fp(self):
        self.log_fp.close()

    def get_batch_sn(self):
        
        self.loged("获取批次号")

        if self.batch_sn is not None:
            return
        
        url_batch_sn = f"{self.host}/v2/datasets/{self.ds_id}/batches"
        headers = {"Access-Key": self.ak}
        params = {"dataset_id": self.ds_id}
        json_data = {
           "url_batch_sn": url_batch_sn,
           "headers": headers,
           "params": params,
           "method": "post"
        }
        record_json(json_data, self.batch_sn_request_record_path)
        r, errors, success_flag = retry_fuction(self.retry_count, requests.post, url_batch_sn, params=params, headers=headers)
        if not success_flag:
            record_error(errors, self.error_record_path)
            raise Exception(f"expect error: 获取批次号出错")
        try:
            assert r.status_code == 200
            res = r.json()
            record_json(res, self.batch_sn_request_res_path)
            self.batch_sn = res["data"]["batch_sn"]
        except Exception as e:
            raise Exception(f"expect error: 获取批次号出错")

    def get_oss_config(self):
        
        self.loged("获取云存储配置")
        
        url_oss_config = f"{self.host}/v2/datasets/{self.ds_id}/oss-config"
        headers = {"Access-Key": self.ak, "User-Agent": "apifox/1.0.0"}
        params = {"dataset_id": self.ds_id, "upload_flag": "bucket_default"}
        json_data = {
           "url_oss_config": url_oss_config,
           "headers": headers,
           "params": params,
           "method": "get"
        }
        record_json(json_data, self.oss_config_request_record_path)
        
        r, errors, success_flag = retry_fuction(self.retry_count, requests.get, url_oss_config, params=params, headers=headers)
        if not success_flag:
            record_error(errors, self.error_record_path)
            raise Exception(f"expect error: 获取云存储配置出错")

        try:
            assert r.status_code == 200
            res = r.json()
            record_json(res, self.oss_config_request_res_path)
            
            self.oss_config = res["data"]
            if self.oss_config["oss_type"] == "minio":
                self.oss_config["bucket"] = BUCKET

            self.get_upload_class()

        except Exception as e:
            raise Exception(f"expect error: 获取云存储配置出错")

    def get_id(self):
        
        self.loged("获取id")
        

        timestamp = str(int(time.time()))
        uuid_str = str(uuid.uuid4())
        uuid_str_head = uuid_str[:10]

        url_id = (
            f"{self.host}/v2/datasets/{self.ds_id}/batches/{self.batch_sn}/files"
        )
        headers = {"Access-Key": self.ak, "Content-Type": "application/json"}
        json = [
            {
                "name": f"{timestamp}__{uuid_str}.zip",
                "path": f"{timestamp}__{uuid_str}.zip",
                "batch_file_status": 1,
                "size": 1,
                "md5": f"{timestamp}{uuid_str_head}",
            }
        ]

        json_data = {
           "url_id": url_id,
           "headers": headers,
           "json": json,
           "method": "post"
        }
        record_json(json_data, self.id_request_record_path)
        r, errors, success_flag = retry_fuction(self.retry_count, requests.post, url_id, json=json, headers=headers)
        if not success_flag:
            record_error(errors, self.error_record_path)
            raise Exception(f"expect error: 获取id出错")
        try:
            assert r.status_code == 200
            res = r.json()
            record_json(res, self.id_request_res_path)
            self.id = res["data"]["id"]
        except Exception as e:
            raise Exception(f"expect error: 获取id出错")

    def ignore(self, name):
        # 隐藏文件 mac文件
        if name.startswith(".") or name == "__MACOSX":
            return True
        else:
            return False

    def check_file_root(self, file_root, file_types, error_str):
        files_ = os.listdir(file_root)
        files_info = {}
        for file in files_:

            if self.ignore(file):
                continue
        
            file_path = self.path_join(file_root, file)

            self.is_file(file_path)

            file_type = self.get_file_type(file_path)
            if file_type not in file_types:
                error_path = self.get_relative_path(file_path)
                raise Exception(f"expect error: {error_path} {error_str}")

            file_name = self.get_file_name(file_path)

            if file_name in files_info:
                error_path = self.get_relative_path(file_path)
                file_path_with_same_name = files_info[file_name]["file_path"]
                error_path_ = self.get_relative_path(file_path_with_same_name)
                raise Exception(f"expect error: {error_path} {error_path_} 同名文件")

            files_info[file_name] = {
                "file_type": file_type,
                "file_path": file_path,
                "file": file,
            }

        return files_info

    def get_relative_path(self, path):
        return path[len(os.path.dirname(self.data_root)) + 1 :]

    def get_file_type(self, file_path):
        try:
            file_type = os.path.splitext(file_path)[1][1:].lower()
            return file_type
        except Exception as e:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"expect error: {error_path} 获取文件类型失败")

    def get_file_name(self, file_path):
        try:
            file = os.path.basename(file_path)
            file_name = os.path.splitext(file)[0]
            return file_name
        except Exception as e:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"expect error: {error_path} 获取文件名称失败")

    def is_file(self, file_path):
        if not os.path.isfile(file_path):
            error_path = self.get_relative_path(file_path)
            raise Exception(f"expect error: {error_path} 应为文件")
        return True

    def is_root(self, file_root):
        if not os.path.isdir(file_root):
            error_path = self.get_relative_path(file_root)
            raise Exception(f"expect error: {error_path} 应为目录")
        return True

    # 获取序列目录
    def get_segment_roots(self):
        segment_names_ = os.listdir(self.data_root)

        segment_roots = []

        for segment_name in segment_names_:

            if self.ignore(segment_name):
                continue

            segment_root = self.path_join(self.data_root, segment_name)

            if os.path.isfile(segment_root):
                error_path = self.get_relative_path(segment_root)
                raise Exception(f"expect error: 错误文件:{error_path},应为序列目录")

            segment_roots.append(segment_root)

        if len(segment_roots) == 0:
            raise Exception("expect error: 序列目录数量为0")

        segment_roots.sort()

        return segment_roots
    
    def get_md5_cache_path(self, file_path):
        return self.upload_cache_root + "/" + self.get_relative_path(file_path) + "/.md5_" + self.get_file_modify_time(file_path)
    
    def get_pic_cache_path(self, file_path):
        return self.upload_cache_root + "/" + self.get_relative_path(file_path) + "/.pic_" + self.get_file_modify_time(file_path)
    
    def str_compare(self, a, b):
        if str(a) == str(b):
            return True
        else:
            return False
        
    def write_cache(self, cache, cache_path):
        self.make_dir(cache_path)
        with open(cache_path, 'wb') as f:
            f.write(cache.encode('utf-8'))
            f.write(bytes([0,0,0,0]))
    
    def read_cache(self, cache_path):
        with open(cache_path, 'rb') as f:
            buf = f.read()
        if not (len(buf) > 4 and buf[-1]==0 and buf[-2]==0 and buf[-3]==0 and buf[-4]==0):
            return None, False
        else:
            return buf[:-4].decode("utf-8"), True
    
    def get_file_md5_(self, file_path):
        with open(file_path, "rb") as f:
            buffer = f.read()
        file_md5 = hashlib.md5(buffer).hexdigest()
        return file_md5

    def get_file_md5(self, file_path):
        try:
            md5_cache_path = self.get_md5_cache_path(file_path)
            if self.use_cache:
                if os.path.exists(md5_cache_path):
                    file_md5, flag = self.read_cache(md5_cache_path)
                    if not flag:
                        file_md5 = self.get_file_md5_(file_path)
                else:
                    file_md5 = self.get_file_md5_(file_path)
            else:
                file_md5 = self.get_file_md5_(file_path)

            if self.save_cache:
                self.write_cache(file_md5, md5_cache_path)

            return file_md5
        except Exception as e:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"expect error: {error_path} 获取文件md5失败")

    def get_file_size(self, file_path):
        try:
            file_size = os.path.getsize(file_path)
            remainder = file_size % 1024
            file_size = int(file_size / 1024)
            if remainder > 0:
                file_size += 1
            return file_size
        except Exception as e:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"expect error: {error_path} 获取文件大小失败")

    def get_pic_size_(self, pic_file_path):
        img = Image.open(pic_file_path)
        w = img.width
        h = img.height
        img.close()
        pic_size = str(w) + "*" + str(h)
        return pic_size

    def get_pic_size(self, pic_file_path):
        try:
            pic_cache_path = self.get_pic_cache_path(pic_file_path)
            if self.use_cache:
                if os.path.exists(pic_cache_path):
                    pic_size, flag = self.read_cache(pic_cache_path)
                    if not flag:
                        pic_size = self.get_pic_size_(pic_file_path)
                else:
                    pic_size = self.get_pic_size_(pic_file_path)
            else:
                pic_size = self.get_pic_size_(pic_file_path)
            
            if self.save_cache:
                self.write_cache(pic_size, pic_cache_path)
            return pic_size
        
        except Exception as e:
            error_path = self.get_relative_path(pic_file_path)
            raise Exception(f"expect error: {error_path} 获取图像尺寸失败")
    
    def get_file_modify_time(self, filePath):
        try:
            t = os.path.getmtime(filePath)
            return str(t)
        except Exception as e:
            error_path = self.get_relative_path(filePath)
            raise Exception(f"expect error: {error_path} 获取文件修改时间失败")

    def make_dir(self, file_path):
        file_root = os.path.dirname(file_path)
        if not os.path.exists(file_root):
            os.makedirs(file_root)

    def segment_split(self, file_types):
        
        if self.package_count is None:
            return
        if self.debug:
            print("分包")
        
        self.upload_files_count = 0

        new_upload_files_path = {}
        for segment_relative_root in self.upload_files_path.keys():
            segment_name = os.path.basename(segment_relative_root)
            files = {}
            for file_relative_path in self.upload_files_path[segment_relative_root].keys():
                file_name = self.get_file_name(file_relative_path)
                file_type = self.get_file_type(file_relative_path)
      
                if file_name not in files:
                    files[file_name] = {
                        "file": [],
                        "pre_label": []
                    }
                if file_type in file_types:
                    files[file_name]["file"].append(file_relative_path)
                    files[file_name]["file"].append(self.upload_files_path[segment_relative_root][file_relative_path])
                else:
                    files[file_name]["pre_label"].append(file_relative_path)
                    files[file_name]["pre_label"].append(self.upload_files_path[segment_relative_root][file_relative_path])

            file_index = -1
            for file_name in sorted(files.keys()):
                file_index += 1
                new_segment_name = segment_name + PACKAGE_SPECIAL_STRING + str(file_index // self.package_count).rjust(5,"0")
                new_segment_relative_root = self.path_join(os.path.dirname(segment_relative_root), new_segment_name)

                for k, v in files[file_name].items():
                    for index, _ in enumerate(files[file_name][k]):
                        if index % 2 != 0:
                            continue
                        if new_segment_relative_root not in new_upload_files_path:
                            new_upload_files_path[new_segment_relative_root] = {}    
                        new_upload_files_path[new_segment_relative_root][files[file_name][k][index]] = files[file_name][k][index+1]
                        self.upload_files_count += 1

        self.upload_files_path = new_upload_files_path

    # 获取单个文件信息
    def get_file_info(self, file_path, is_pic=False, size_md5=True):
        name = os.path.basename(file_path)
        if size_md5:
            size = self.get_file_size(file_path)
            md5 = self.get_file_md5(file_path)
        else:
            size = None
            md5 = None
        file_info = {
            "sequence_id": "",
            "name": name,
            "path": "",
            "path_original": file_path,
            "size": size,
            "md5": md5,
            "status": "fail",
            "remark": "未上传",
            "order_sn": "",
        }
        if is_pic:
            file_info["pic_size"] = self.get_pic_size(file_path)
        
        return file_info

    # 循环文件列表添加每一个文件的文件序数
    def add_order_sn_and_sequence_id(self):
        
        self.loged("获取文件id")
        segment_id = -1
        for segment_relative_root in sorted(self.upload_files_path.keys()):
            segment_id += 1

            file_id = -1
            for file_relative_path in sorted(
                self.upload_files_path[segment_relative_root].keys()
            ):
                file_id += 1
                self.upload_files_path[segment_relative_root][file_relative_path][
                    "order_sn"
                ] = str(segment_id).rjust(5, "0") + str(file_id).rjust(5, "0")
                self.upload_files_path[segment_relative_root][file_relative_path][
                    "sequence_id"
                ] = str(segment_id).rjust(5, "0")

    def add_oss_file_path(self):
        
        self.loged("获取云存储路径")
        for segment_relative_root in self.upload_files_path.keys():
            new_segment_name = os.path.basename(segment_relative_root)
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
                if self.package_count is not None:
                    alls = file_relative_path.split("/")
                    alls[1] = new_segment_name
                    file_relative_path_ = "/".join(alls)
                else:
                    file_relative_path_ = file_relative_path
                if self.oss_config["oss_type"] == "ali_oss":
                    oss_path = (
                        f"/{BUCKET}/{self.ds_id}/{self.batch_sn}/{file_relative_path_}"
                    )
                else:
                    bucket_name = self.oss_config["bucket"]
                    oss_path = f"/{bucket_name}/{self.ds_id}/{self.batch_sn}/{file_relative_path_}"
                self.upload_files_path[segment_relative_root][file_relative_path][
                    "path"
                ] = oss_path
    
    def get_upload_cache_path(self, local_file_path, oss_file_path):
        return self.upload_cache_root + "/" + self.get_relative_path(local_file_path) + "/.upload_" + hashlib.md5((self.get_file_modify_time(local_file_path) + oss_file_path).encode("utf-8")).hexdigest()

    def upload_file(self, segment_relative_root, file_relative_path):
        file_info = self.upload_files_path[segment_relative_root][file_relative_path]
        oss_file_path = file_info["path"]
        local_file_path = file_info["path_original"]

        upload_cache_path = self.get_upload_cache_path(local_file_path, oss_file_path)
        if self.use_cache:
            if not os.path.exists(upload_cache_path):
                self.oss_class.upload(oss_file_path, local_file_path, self.oss_config)
        else:
            self.oss_class.upload(oss_file_path, local_file_path, self.oss_config)
        
        if self.save_cache:
            self.write_cache("1", upload_cache_path)

        self.secure_debug(local_file_path, oss_file_path)

    def upload_files(self):
        
        self.loged("开始上传文件")

        record_json(self.upload_files_path, self.file_list_pre_upload_record_path)

        for segment_relative_root in self.upload_files_path.keys():
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
                fs = self.executor.execute(
                    self.upload_file, (segment_relative_root, file_relative_path)
                )
                self.executor_functions.append(
                    [fs, self.upload_file, (segment_relative_root, file_relative_path)]
                )
        self.retry_function_execution()
        
        record_json(self.upload_files_path, self.file_list_pre_upload_res_path)

    def secure_debug(self, local_file_path, oss_file_path):
        flag_uploaded_files_count_change = False
        try:
            self.lock.acquire()

            self.uploaded_files_count += 1
            flag_uploaded_files_count_change = True

            
            debug_path = self.get_relative_path(local_file_path)
            self.loged(
                f"上传: {self.uploaded_files_count}/{self.upload_files_count} {debug_path} --> {oss_file_path}"
            )

        except Exception as e:
            if flag_uploaded_files_count_change:
                self.uploaded_files_count -= 1
            raise e
        finally:
            self.lock.release()

    def retry_function_execution(self):

        retry_count = self.retry_count
        while retry_count:

            old_executor_functions = self.executor_functions
            new_executor_functions = []
            total_count = len(old_executor_functions)

            while True:
                success_count = 0
                fail_count = 0
                for function in old_executor_functions:
                    if function[0].exception():
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "status"
                        ] = "fail"
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "remark"
                        ] = str(function[0].exception())
                        fail_count += 1
                    elif function[0].done():
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "status"
                        ] = "suc"
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "remark"
                        ] = ""
                        success_count += 1
                if success_count + fail_count == total_count:
                    break
                time.sleep(1)

            
            upload_round_count = self.retry_count - retry_count + 1
            self.loged(
                f"第{upload_round_count}轮上传: 总和:{total_count}, 成功:{success_count}, 失败:{fail_count}"
            )

            for function in old_executor_functions:
                if function[0].exception():
                    fs = self.executor.execute(function[1], function[2])
                    new_executor_functions.append([fs, function[1], function[2]])

            self.executor_functions = new_executor_functions
            retry_count -= 1

            if fail_count == 0:
                break

        if fail_count != 0:
            old_executor_functions = self.executor_functions
            total_count = len(self.executor_functions)
            while True:
                success_count = 0
                fail_count = 0
                for function in old_executor_functions:
                    if function[0].exception():
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "status"
                        ] = "fail"
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "remark"
                        ] = str(function[0].exception())
                        fail_count += 1
                    elif function[0].done():
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "status"
                        ] = "suc"
                        self.upload_files_path[function[2][0]][function[2][1]][
                            "remark"
                        ] = ""
                        success_count += 1
                if success_count + fail_count == total_count:
                    break
                time.sleep(1)

        self.fail_uploaded_files_count = fail_count
        self.success_uploaded_files_count = (
            self.upload_files_count - self.fail_uploaded_files_count
        )

        
        if fail_count != 0:
            upload_round_count = self.retry_count - retry_count + 1
            self.loged(
                f"第{upload_round_count}轮上传: 总和:{total_count}, 成功:{success_count}, 失败:{fail_count}"
            )

        if self.fail_uploaded_files_count != 0:
            self.loged(
                f"上传失败, 总和:{self.upload_files_count}, 成功:{self.success_uploaded_files_count}, 失败:{self.fail_uploaded_files_count}"
            )
        else:
            self.loged(
                f"上传成功, 总和:{self.upload_files_count}, 成功:{self.success_uploaded_files_count}, 失败:{self.fail_uploaded_files_count}"
            )

    def change_path_original(self):
        for segment_relative_root in self.upload_files_path.keys():
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
                self.upload_files_path[segment_relative_root][file_relative_path]["path_original"] = self.upload_files_path[segment_relative_root][file_relative_path]["path"]

    def call_back_fail(self, e):
        return
        self.error_callback_url = f"{self.host}/v2/datasets/{self.ds_id}/upload-errors"
        headers = {
            "Content-Type": "application/json",
            "Access-Key": self.ak,
        }
        error_str = str(e)
        if error_str.startswith("expect error: "):
            error_str = error_str[14:]
        data = {"batch_sn": self.batch_sn, "msg": error_str}
        json_data = {
            "error_callback_url": self.error_callback_url,
            "headers": headers,
            "json": data,
            "method": "post"
        }        
        try:
            record_json(json_data,self.call_back_fail_record_path)
        except Exception as record_e:
            record_error(record_e, self.error_record_path)

        res, errors, success_flag = retry_fuction(self.retry_count, requests.post, self.error_callback_url, json=data, timeout=20, headers=headers)
        
        if not success_flag:
            record_error(error_str, self.error_record_path)
            record_error(errors, self.error_record_path)
            error_str = "expect error: 回调错误接口失败"
            raise_error(error_str)

    def call_back_success(self):
        self.callback_url = (
            f"{self.host}/v2/datasets/{self.ds_id}/processed-files/{self.batch_sn}"
        )
        files = []
        for segment_relative_root in self.upload_files_path.keys():
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
                files.append(
                    self.upload_files_path[segment_relative_root][file_relative_path]
                )
        files_total_count = len(files)

        headers = {
            "Content-Type": "application/json",
            "Access-Key": self.ak,
        }

        json_data = {
            "callback_url": self.callback_url,
            "json": {
                "id": self.id,
                "ds_id": self.ds_id,
                "batch_sn": self.batch_sn,
                "process_type": self.process_type,
                "path": "",
                "files_total_count": files_total_count,
                "files": files,
            },
            "headers": headers,
            "method": "post"
        }

        try:
            record_json(json_data, self.call_back_success_record_path)
        except Exception as record_e:
            record_error(record_e, self.error_record_path)
        

        count = files_total_count // CALL_BACK_SUCCESS_COUNT
        if files_total_count % CALL_BACK_SUCCESS_COUNT != 0:
            count += 1

        for i in range(count):
            if i != count -1:
                files_part = files[i*CALL_BACK_SUCCESS_COUNT:i*CALL_BACK_SUCCESS_COUNT+CALL_BACK_SUCCESS_COUNT]
            else:
                files_part = files[i*CALL_BACK_SUCCESS_COUNT:]
            
            data = {
                "id": self.id,
                "ds_id": self.ds_id,
                "batch_sn": self.batch_sn,
                "process_type": self.process_type,
                "path": "",
                "files_total_count": files_total_count,
                "files": files_part,
            }
            
            res, errors, success_flag = retry_fuction(self.retry_count, requests.post, self.callback_url, json=data, timeout=20, headers=headers)

            if not success_flag:
                record_error(errors, self.error_record_path)
                raise Exception("expect error: 提交文件列表失败")
