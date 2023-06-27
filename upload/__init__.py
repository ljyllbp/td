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
import pathlib

from config import *
from utils import oss, executor

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


class upload(object):
    def __init__(self, ds_id, data_root):
        self.data_root = data_root.replace("\\","/").replace("//","/")

        self.debug = False
        self.upload_files_path = {}
        self.add_files_path = []
        self.add_file_name = ".add_record.json"
        self.move_files = {}

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

        self.uploaded_files_count = 0  # 已经下载的文件数量
        self.upload_files_count = 0  # 需要下载的文件数量
        self.success_uploaded_files_count = 0  # 成功下载的数量
        self.fail_uploaded_files_count = 0  # 失败下载的数量

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

    def set_executor(self, thread_num):
        self.executor = executor.Executor(thread_num)
    
    def set_pcd_option(self, is_simplify_pcd, is_force_Compressed):
        self.is_simplify_pcd = is_simplify_pcd
        self.is_force_Compressed = is_force_Compressed
    
    def save_add_files(self):
        with open(self.data_root+"/"+ self.add_file_name, "w", encoding="utf-8") as f:
            json.dump(self.add_files_path, f, ensure_ascii=False)
    
    @staticmethod
    def get_data_type(host, ds_id, ak):
        url_ds_info = f"{host}/v2/datasets/{ds_id}"
        headers = {"Access-Key": ak, "User-Agent": "apifox/1.0.0"}
        r = requests.get(url_ds_info, headers=headers)
        assert r.status_code == 200
        res = r.json()
        return res["data"]["data_type"]

    def assert_illegal_characters(self, path):
        for character in ILLEGAL_CHARACTER:
            if character in path:
                raise Exception(f"{path} 路径中不允许出现特殊字符'{character}'")
        try:
            path.encode("utf-8")
        except:
            raise Exception(f"{path} 请使用符合规范的UTF-8字符")

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
        if self.debug:
            print("删除过程数据")
        if os.path.exists(self.data_root+"/"+ self.add_file_name):
            with open(self.data_root+"/"+ self.add_file_name, "r", encoding="utf-8") as f:
                add_files_path = json.load(f)
                for add_file_path in add_files_path:
                    if os.path.exists(add_file_path):
                        if os.path.isfile(add_file_path):
                            os.remove(add_file_path)
                        else:
                            shutil.rmtree(add_file_path)
            os.remove(self.data_root+"/"+ self.add_file_name)

    def get_upload_class(self):
        if self.oss_config["oss_type"] == "ali_oss":
            self.oss_class = oss.AliyunClass()
        else:
            self.oss_class = oss.MinioClass()

    def get_batch_sn(self):
        if self.debug:
            print("获取批次号")
        try:
            url_batch_sn = f"{self.host}/v2/datasets/{self.ds_id}/batches"
            headers = {"Access-Key": self.ak}
            params = {"dataset_id": self.ds_id}
            r = requests.post(url_batch_sn, params=params, headers=headers)
            assert r.status_code == 200
            res = r.json()
            # if self.debug:
            #     print(json.dumps(res))
            self.batch_sn = res["data"]["batch_sn"]
        except Exception as e:
            raise Exception(f"获取批次号出错:{str(e)}")

    def get_oss_config(self):
        if self.debug:
            print("获取云存储配置")
        try:
            url_oss_config = f"{self.host}/v2/datasets/{self.ds_id}/oss-config"

            headers = {"Access-Key": self.ak, "User-Agent": "apifox/1.0.0"}
            params = {"dataset_id": self.ds_id, "upload_flag": "bucket_default"}
            r = requests.get(url_oss_config, params=params, headers=headers)
            assert r.status_code == 200
            res = r.json()
            # if self.debug:
            #     print(json.dumps(res))
            
            self.oss_config = res["data"]
            if self.oss_config["oss_type"] == "minio":
                self.oss_config["bucket"] = BUCKET

            self.get_upload_class()
        except Exception as e:
            raise Exception(f"获取云存储配置出错:{str(e)}")

    def get_id(self):
        if self.debug:
            print("获取id")
        try:

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

            r = requests.post(url_id, json=json, headers=headers)
            assert r.status_code == 200
            res = r.json()
            if self.debug:
                print(json.dumps(res))
            self.id = res["data"]["id"]

        except Exception as e:
            raise Exception(f"获取id出错:{str(e)}")

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
        
            file_path = os.path.join(file_root, file)

            self.is_file(file_path)

            file_type = self.get_file_type(file_path)
            if file_type not in file_types:
                error_path = self.get_relative_path(file_path)
                raise Exception(f"{error_path} {error_str}")

            file_name = self.get_file_name(file_path)

            if file_name in files_info:
                error_path = self.get_relative_path(file_path)
                file_path_with_same_name = files_info[file_name]["file_path"]
                error_path_ = self.get_relative_path(file_path_with_same_name)
                raise Exception(f"{error_path} {error_path_} 同名文件")

            files_info[file_name] = {
                "file_type": file_type,
                "file_path": file_path,
                "file": file,
            }

        return files_info

    def get_relative_path(self, path):
        return path[len(os.path.dirname(self.data_root)) + 1 :].replace("\\","/").replace("//","/")

    def get_file_type(self, file_path):
        try:
            file_type = os.path.splitext(file_path)[1][1:].lower()
            return file_type
        except:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"{error_path} 获取文件类型失败")

    def get_file_name(self, file_path):
        try:
            file = os.path.basename(file_path)
            file_name = os.path.splitext(file)[0].lower()
            return file_name
        except:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"{error_path} 获取文件名称失败")

    def is_file(self, file_path):
        if not os.path.isfile(file_path):
            error_path = self.get_relative_path(file_path)
            raise Exception(f"{error_path} 应为文件")
        return True

    def is_root(self, file_root):
        if not os.path.isdir(file_root):
            error_path = self.get_relative_path(file_root)
            raise Exception(f"{error_path} 应为目录")
        return True

    # 获取序列目录
    def get_segment_roots(self):
        segment_names_ = os.listdir(self.data_root)

        segment_roots = []

        for segment_name in segment_names_:

            if self.ignore(segment_name):
                continue

            segment_root = os.path.join(self.data_root, segment_name)

            if os.path.isfile(segment_root):
                error_path = self.get_relative_path(segment_root)
                raise Exception(f"错误文件:{error_path},应为序列目录")

            segment_roots.append(segment_root)

        if len(segment_roots) == 0:
            raise Exception("序列目录数量为0")

        segment_roots.sort()

        return segment_roots

    def get_file_md5(self, file_path):
        try:
            with open(file_path, "rb") as f:
                buffer = f.read()
            file_md5 = hashlib.md5(buffer).hexdigest()
            return file_md5
        except:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"{error_path} 获取文件md5失败")

    def get_file_size(self, file_path):
        try:
            file_size = os.path.getsize(file_path)
            remainder = file_size % 1024
            file_size = int(file_size / 1024)
            if remainder > 0:
                file_size += 1
            return file_size
        except:
            error_path = self.get_relative_path(file_path)
            raise Exception(f"{error_path} 获取文件大小失败")

    def get_pic_size(self, pic_file_path):
        try:
            img = Image.open(pic_file_path)
            w = img.width
            h = img.height
            img.close()
            return str(w) + "*" + str(h)
        except:
            error_path = self.get_relative_path(pic_file_path)
            raise Exception(f"{error_path} 获取图像尺寸失败")
    
    def make_dir(self, file_path):
        file_root = os.path.dirname(file_path)
        if not os.path.exists(file_root):
            os.makedirs(file_root)

    # 获取单个文件信息
    def get_file_info(self, file_path, is_pic=False):
        name = os.path.basename(file_path)
        size = self.get_file_size(file_path)
        md5 = self.get_file_md5(file_path)
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
        if self.debug:
            print("获取文件id")
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
        if self.debug:
            print("获取云存储路径")
        for segment_relative_root in self.upload_files_path.keys():
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
                file_relative_path = file_relative_path.replace("\\","/").replace("//","/")
                if self.oss_config["oss_type"] == "ali_oss":
                    oss_path = (
                        f"/{BUCKET}/{self.ds_id}/{self.batch_sn}/{file_relative_path}"
                    )
                else:
                    bucket_name = self.oss_config["bucket"]
                    oss_path = f"/{bucket_name}/{self.ds_id}/{self.batch_sn}/{file_relative_path}"
                self.upload_files_path[segment_relative_root][file_relative_path][
                    "path"
                ] = oss_path

    def upload_file(self, segment_relative_root, file_relative_path):
        file_info = self.upload_files_path[segment_relative_root][file_relative_path]
        oss_file_path = file_info["path"]
        local_file_path = file_info["path_original"]
        self.oss_class.upload(oss_file_path, local_file_path, self.oss_config)
        self.secure_debug(local_file_path)

    def upload_files(self):
        if self.debug:
            print("开始上传文件")
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

    def secure_debug(self, local_file_path):
        flag_uploaded_files_count_change = False
        try:
            self.lock.acquire()

            self.uploaded_files_count += 1
            flag_uploaded_files_count_change = True

            if self.debug:
                debug_path = self.get_relative_path(local_file_path)
                print(
                    f"上传: {self.uploaded_files_count}/{self.upload_files_count} {debug_path}"
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

            if self.debug:
                upload_round_count = self.retry_count - retry_count + 1
                print(
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

        if self.debug:
            if fail_count != 0:
                upload_round_count = self.retry_count - retry_count + 1
                print(
                    f"第{upload_round_count}轮上传: 总和:{total_count}, 成功:{success_count}, 失败:{fail_count}"
                )

            if self.fail_uploaded_files_count != 0:
                print(
                    f"上传失败, 总和:{self.upload_files_count}, 成功:{self.success_uploaded_files_count}, 失败:{self.fail_uploaded_files_count}"
                )
            else:
                print(
                    f"上传成功, 总和:{self.upload_files_count}, 成功:{self.success_uploaded_files_count}, 失败:{self.fail_uploaded_files_count}"
                )

    def change_path_original(self):
        for segment_relative_root in self.upload_files_path.keys():
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
                self.upload_files_path[segment_relative_root][file_relative_path]["path_original"] = self.upload_files_path[segment_relative_root][file_relative_path]["path"]

    def call_back_fail(self, e):
        self.error_callback_url = f"{self.host}/v2/datasets/{self.ds_id}/upload-errors"
        headers = {
            "Content-Type": "application/json",
            "Access-Key": self.ak,
        }
        data = {"batch_sn": self.batch_sn, "msg": str(e)}
        r = requests.post(
            self.error_callback_url, json=data, timeout=20, headers=headers
        )

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
        data = {
            "id": self.id,
            "ds_id": self.ds_id,
            "batch_sn": self.batch_sn,
            "process_type": self.process_type,
            "path": "",
            "files_total_count": len(files),
            "files": files,
        }

        headers = {
            "Content-Type": "application/json",
            "Access-Key": self.ak,
        }
       
        r = requests.post(self.callback_url, json=data, timeout=20, headers=headers)

        assert r.status_code == 200