import os
import requests
import json
import shutil
from urllib import parse
import threading
import time
from utils import executor
from utils.pulic_tool import raise_error, record_error

class Exporter(object):
    def __init__(self,out,task_batch_key,ak,host="http://label-std.testin.cn",download_type="label",have_more_info=False,debug=True):
        # |名称|位置|类型|必选|说明|
        # |---|---|---|---|---|
        # |work_type|query|int|否|工序 1：标注，2：审核，3：质检，4：验收，选择状态时此字段必传|
        # |status|query|int|否|状态 0：待处理，1：进行中，2：已通过，3：已驳回，未传状态则返回全部数据|
        # |package_id|query|int|否|题包id|
        # |task_id|query|int|否|子题id|
        # |file_name|query|string|否|文件名称，暂时支持左匹配模糊查询|
        # download_type str label(标注结果)/original(原始文件)/original_and_label(标注结果加原始文件)

        self.out = out.replace("\\","/").replace("//","/") # 保存路径

        time_str = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()).replace(" ", "_").replace(":","-")
        pre = os.path.expanduser('~') + f"/.td/export/{time_str}/" + os.path.basename(out)
        self.error_record_path = f"{pre}/error.txt"
        self.log_path = f"{pre}/log"
        self.log_fp = self.get_log_fp()

        self.task_batch_key = task_batch_key # 任务key
        self.ak = ak # 密钥
        self.host = host # host
        self.download_type = download_type # 下载类型
        self.have_more_info = have_more_info # 是否包含非标注信息

        self.debug = debug # 打印

        self.dataset_type = None # 数据集类型
        self.project_key = None # 项目key
        
        self.host_task_list = f"{self.host}/v2/task-batches/{self.task_batch_key}/packages"
        self.items = [] # 中间存储信息
        self.errors = []

        self.work_type = None # 工序
        self.status = None # 工序状态
        self.package_id = None # 包id
        self.task_id = None # 题id
        self.file_name = None # 文件名
        self.operate_work_type = None # 操作工序，和operate_users联合使用，查询某一个人操作的题
        self.operate_users = None # 操作人id，和operate_work_type联合使用，查询某一个人操作的题
        self.seg_dir_name = None # 序列名，支持多个文件名逗号连接查询

        self.downloaded_files_count = 0 # 已经下载的文件数量
        self.download_files_count = 0 # 需要下载的文件数量
        self.success_downloaded_files_count = 0 # 成功下载的数量
        self.fail_downloaded_files_count = 0 # 失败下载的数量
        
        self.executor = executor.Executor() # 多线程
        self.executor_functions = [] 
        self.lock=threading.Lock()
        self.retry_count = 4 # 下载尝试次数

    def set_work_type(self, work_type):
        self.work_type = work_type
    
    def set_status(self, status):
        self.status = status
    
    def set_package_id(self, package_id):
        self.package_id = package_id
    
    def set_task_id(self, task_id):
        self.task_id = task_id
    
    def set_file_name(self, file_name):
        self.file_name = file_name
    

    def set_operate_work_type(self, operate_work_type):
        self.operate_work_type = operate_work_type
    
    def set_operate_users(self, operate_users):
        self.operate_users = operate_users
    
    def set_seg_dir_name(self, seg_dir_name):
        self.seg_dir_name = seg_dir_name


    def set_download_type(self, download_type):
        self.download_type = download_type

    def set_have_more_info(self, have_more_info):
        self.have_more_info = have_more_info

    def set_retry_count(self, retry_count):
        self.retry_count = retry_count
    
    def set_executor(self, thread_num):
        self.executor = executor.Executor(thread_num)

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
    
    def make_dir(self, file_path):
        file_root = os.path.dirname(file_path)
        if not os.path.exists(file_root):
            os.makedirs(file_root)

    def get_params(self, page):
        params = {
            "page": page,
            "is_extension": 1
        }
        if self.work_type != None:
            params["work_type"] = self.work_type
        if self.status != None:
            params["status"] = self.status
        if self.package_id != None:
            params["package_id"] = self.package_id
        if self.task_id != None:
            params["task_id"] = self.task_id
        if self.file_name != None:
            params["file_name"] = self.file_name
        
        if self.operate_work_type != None:
            params["operate_work_type"] = self.operate_work_type
        if self.operate_users != None:
            params["operate_users"] = self.operate_users
        if self.seg_dir_name != None:
            params["seg_dir_name"] = self.seg_dir_name

        return params
    
    def reset_search_criteria(self):
        self.work_type = None
        self.status = None
        self.package_id = None
        self.task_id = None
        self.file_name = None
        self.operate_work_type = None
        self.operate_users = None
        self.seg_dir_name = None
    
    def clear_items(self):
        self.items = []

    def get_items(self):
        try:
            page = 1
            
            params = self.get_params(page)
            
            headers = {"Access-Key": self.ak}
            
            while True:
                params["page"] = page
                r = requests.get(self.host_task_list, params=params, headers=headers)

                assert r.status_code == 200
                res = r.json()
                
                self.dataset_type = res["data"]["dataset_type"]
                
                
                
                self.project_key = res["data"]["project_key"]
                
                for item in res["data"]["items"]:
                    self.items.append(item)
                
                if res["data"]["meta"]["total_num"] % 20 == 0:
                    page_total = int(res["data"]["meta"]["total_num"] / 20)
                else:
                    page_total = int(res["data"]["meta"]["total_num"] / 20) + 1
                
                self.loged(
                    f"task_batch_key:{self.task_batch_key} [DOWNLOAD_ITEMS] pageTotal:{page_total}, current Page:{res['data']['meta']['page']}, per page items:{res['data']['meta']['page_num']}"
                )
                page += 1
                if page > page_total:
                    break
            self.get_download_files_count()
            self.reset_search_criteria()
        except Exception as e:
            record_error(e, self.error_record_path)
            raise_error("expect error: 请检查参数，或下载数为0")

    def download_files(self, overwrite=False):
        try:
            if self.download_type == "label":
                self.download_label_files(overwrite)
            elif self.download_type == "original":
                self.download_original_files(overwrite)
            else:
                self.download_label_files(overwrite)
                self.download_original_files(overwrite)
            self.retry_function_execution()
            if self.dataset_type == "text":
                self.text_files_merge()
        except Exception as e:
            record_error(e, self.error_record_path)
            raise_error("expect error: 下载文件失败") 
    
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
                        fail_count += 1
                    elif function[0].done():
                        success_count += 1
                if success_count + fail_count == total_count:
                    break
                time.sleep(1)
            
            download_round_count = self.retry_count - retry_count + 1
            self.loged(f"task_batch_key:{self.task_batch_key} [DOWNLOAD_BY_ROUND_RESULT] download_round_count:{download_round_count}, total:{total_count}, success:{success_count}, fail:{fail_count}")
            
            for function in old_executor_functions:
                if function[0].exception():
                    fs = self.executor.execute(function[1],function[2])
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
                        fail_count += 1
                    elif function[0].done():
                        success_count += 1
                if success_count + fail_count == total_count:
                    break
                time.sleep(1)

        self.fail_downloaded_files_count = fail_count
        self.success_downloaded_files_count = self.download_files_count - self.fail_downloaded_files_count

        if fail_count != 0:
            download_round_count = self.retry_count - retry_count + 1
            self.loged(f"task_batch_key:{self.task_batch_key} [DOWNLOAD_BY_ROUND_RESULT] download_round_count:{download_round_count}, total:{total_count}, success:{success_count}, fail:{fail_count}")

        if self.fail_downloaded_files_count != 0:
            self.loged(f"task_batch_key:{self.task_batch_key} [DOWNLOAD_RESULT] failed, total:{self.download_files_count}, success:{self.success_downloaded_files_count}, fail:{self.fail_downloaded_files_count}")
        else:
            self.loged(f"task_batch_key:{self.task_batch_key} [DOWNLOAD_RESULT] succeed, total:{self.download_files_count}, success:{self.success_downloaded_files_count}, fail:{self.fail_downloaded_files_count}")

    def get_download_label_files_count(self):
        download_label_files_count = 0
        for item in self.items:
            for task in item["tasks"]:
                download_label_files_count += 1
        return download_label_files_count
    
    def get_download_original_files_count(self):
        download_original_files_count = 0
        for item in self.items:
        
            # 点云config文件
            config_url = item.get("config_url",None)
            if config_url:
                download_original_files_count += 1

            for task in item["tasks"]:
                
                # 原始文件
                download_original_files_count += 1

                # 点云图像文件
                if "camera" in task and isinstance(task["camera"], dict):
                    for camename, pic_info_list in task["camera"].items():
                        for pic_info in pic_info_list:
                            download_original_files_count += 1
                
                # 文本图像
                if "images" in task and isinstance(task["images"], list):
                    for image_url in task["images"]:
                        download_original_files_count += 1
        
        return download_original_files_count
            
    def get_download_files_count(self):

        
        self.loged(f"task_batch_key:{self.task_batch_key} [STATISTICAL_DOWNLOAD_FILES_COUNT] ",end="")
        
        if self.download_type == "label":
            self.download_files_count = self.get_download_label_files_count()

        elif self.download_type == "original":
            
            self.download_files_count = self.get_download_original_files_count()
        else:
            self.download_files_count = self.get_download_label_files_count() + self.get_download_original_files_count()
        
        self.loged(self.download_files_count)

    def download_label_file(self,task,item,overwrite):

        label_save_path = self.get_label_save_path(task["source_url"])
        
        
        flag_downloaded_files_count_change = False
        if not overwrite and os.path.exists(label_save_path):
            debug_str = "DOWNLOAD_LABEL_FILE"
            is_exist = True
            self.secure_debug(debug_str, label_save_path, is_exist)
            return

        label_save_root = os.path.dirname(label_save_path)
        if not os.path.exists(label_save_root):
            os.makedirs(label_save_root)

        task_id = task["task_id"]
        host_label = f"{self.host}/v2/tasks/{task_id}/label"
        headers = {"Access-Key": self.ak}
        r = requests.get(host_label, headers=headers)
        assert r.status_code == 200
        res = r.json()

        if self.have_more_info:
            for k, v in item.items():
                if k == "config_url" or k == "tasks":
                    continue
                res["data"][k] = v
            res["data"]["task_id"] = task["task_id"]
        
        with open(label_save_path, "w", encoding="utf-8") as f:
            json.dump(res["data"], f, ensure_ascii=False, indent=4)
        
        debug_str = "DOWNLOAD_LABEL_FILE"
        is_exist = False
        self.secure_debug(debug_str, label_save_path, is_exist)

    def download_label_files(self, overwrite):
        for item in self.items:
            for task in item["tasks"]:
                fs = self.executor.execute(self.download_label_file,(task,item,overwrite))
                self.executor_functions.append([fs,self.download_label_file,(task,item,overwrite)])
                # self.download_label_file(task,item,overwrite)

    def download_original_file(self,file_url,file_save_path,debug_str,overwrite):

        if not overwrite and os.path.exists(file_save_path):
            is_exist = True
            self.secure_debug(debug_str, file_save_path, is_exist)
            return
            

        file_save_root = os.path.dirname(file_save_path)
        if not os.path.exists(file_save_root):
            os.makedirs(file_save_root)
        
        with requests.get(file_url, stream=True) as r, open(file_save_path, "wb") as f:
            assert r.status_code == 200
            for content in r.iter_content(chunk_size=4 * 1024):
                f.write(content)

        # r = requests.get(file_url)
        # assert r.status_code == 200
        # with open(file_save_path,"wb") as f:
        #     f.write(r.content)

        is_exist = False
        self.secure_debug(debug_str, file_save_path, is_exist)

    def download_original_files(self, overwrite):
        for item in self.items:
            
            # 下载点云config文件
            config_url = item.get("config_url",None)
            if config_url:
                config_save_path = self.get_source_save_path(config_url)

                debug_str = "DOWNLOAD_POINTCLOUD_CONFIG_FILE"
                fs = self.executor.execute(self.download_original_file,(config_url,config_save_path,debug_str,overwrite))
                self.executor_functions.append([fs,self.download_original_file,(config_url,config_save_path,debug_str,overwrite)])
                # self.download_original_file(config_url,config_save_path,debug_str,overwrite)
                
            for task in item["tasks"]:
                
                # 下载原始文件
                source_url = task["source_url"]
                source_save_path = self.get_source_save_path(source_url)
                debug_str = "DOWNLOAD_SOURCE_FILE"
                fs = self.executor.execute(self.download_original_file,(source_url,source_save_path,debug_str,overwrite))
                self.executor_functions.append([fs,self.download_original_file,(source_url,source_save_path,debug_str,overwrite)])
                # self.download_original_file(source_url,source_save_path,debug_str,overwrite)

                # 下载点云图片文件
                if "camera" in task and isinstance(task["camera"], dict):
                    for camename, pic_info_list in task["camera"].items():
                        for pic_info in pic_info_list:
                            pic_url = pic_info["url"]
                            
                            pic_save_path = self.get_source_save_path(pic_url)

                            debug_str = "DOWNLOAD_POINTCLOUD_CAMERA_FILE"

                            fs = self.executor.execute(self.download_original_file,(pic_url,pic_save_path,debug_str,overwrite))
                            self.executor_functions.append([fs,self.download_original_file,(pic_url,pic_save_path,debug_str,overwrite)])
                            
                            # self.download_original_file(pic_url,pic_save_path,debug_str,overwrite)

                # 下载文本图像
                if "images" in task and isinstance(task["images"], list):
                    for image_url in task["images"]:

                        image_save_path = self.get_source_save_path(image_url)

                        debug_str = "DOWNLOAD_TEXT_IMAGE_FILE"

                        fs = self.executor.execute(self.download_original_file,(image_url,image_save_path,debug_str,overwrite))
                        self.executor_functions.append([fs,self.download_original_file,(image_url,image_save_path,debug_str,overwrite)])
                        # self.download_original_file(image_url,image_save_path,debug_str,overwrite)

    def secure_debug(self, debug_str, save_path, is_exist):
        flag_downloaded_files_count_change = False
        try:
            self.lock.acquire()

            self.downloaded_files_count += 1
            flag_downloaded_files_count_change = True
            
            debug_path = self.get_debug_path(save_path)
            if is_exist:
                self.loged(f"task_batch_key:{self.task_batch_key} [{debug_str}] {self.downloaded_files_count}/{self.download_files_count} {debug_path} already exists")
            else:
                self.loged(f"task_batch_key:{self.task_batch_key} [{debug_str}] {self.downloaded_files_count}/{self.download_files_count} {debug_path}")
        except Exception as e:
            if flag_downloaded_files_count_change:
                self.downloaded_files_count -= 1
            raise e
        finally:
            self.lock.release()
        
    def get_label_save_path(self, source_url):
        if "?" in source_url:
            source_url = parse.unquote(source_url.split("?")[0])
        else:
            source_url = parse.unquote(source_url)
        source_save_path = self.out + "/" + "/".join(source_url.split("/")[4:])
        label_save_path = "/".join(source_save_path.split("/")[:-2]) + "/label/" + os.path.splitext(source_save_path.split("/")[-1])[0] + ".json"
        return label_save_path
    
    def get_source_save_path(self, source_url):
        if "?" in source_url:
            source_url = parse.unquote(source_url.split("?")[0])
        else:
            source_url = parse.unquote(source_url)
        source_save_path = self.out + "/" + "/".join(source_url.split("/")[4:])
        return source_save_path
    
    def get_debug_path(self, path):
        debug_path = path[len(self.out) + 1:]
        return debug_path
    
    def save_items(self):

        items_save_path = self.out + "/" + self.task_batch_key + ".json"

        debug_path = self.get_debug_path(items_save_path)
        
        self.loged(f"task_batch_key:{self.task_batch_key} [SAVE_ITEMS] {debug_path}")

        items_save_root = os.path.dirname(items_save_path)
        if not os.path.exists(items_save_root):
            os.makedirs(items_save_root)
        with open(items_save_path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4)
    
    def load_items(self):

        items_load_path = self.out + "/" + self.task_batch_key + ".json"

        debug_path = self.get_debug_path(items_load_path)
        
        self.loged(f"task_batch_key:{self.task_batch_key} [LOAD_ITEMS] {debug_path}")

        with open(items_load_path, "r", encoding="utf-8") as f:
            self.items = json.load(f)
        
        self.get_download_files_count()
    
    def text_files_merge(self):
        data = {}
        for root, _, filesl in os.walk(self.out):
            for file in filesl:
                if file.endswith('.json'):
                    name = int(file.split('.')[0])
                    json_path = os.path.join(root, file)
                    data_type = os.path.basename(root)
                    base_dir_name = os.path.dirname(root)
                    if base_dir_name not in data:
                        data[base_dir_name] = {}
                        data[base_dir_name][data_type] = {}
                    else:
                        if data_type not in data[base_dir_name]:
                            data[base_dir_name][data_type] = {}
                    data[base_dir_name][data_type][name] = json_path
                else:
                    name = os.path.basename(root)
                    file_path = os.path.join(root, file)
                    data_type = os.path.basename(os.path.dirname(root))
                    base_dir_name = os.path.dirname(os.path.dirname(root))
                    if base_dir_name not in data:
                        data[base_dir_name] = {}
                    if data_type not in data[base_dir_name]:
                        data[base_dir_name][data_type] = []
                    data[base_dir_name][data_type].append(file_path)
        for key, values in data.items():
            text_data = []
            label_data = []
            for k, v in values.items():
                root = os.path.dirname(key)
                name = os.path.basename(key)
                if k == "label":
                    out = os.path.join(root, 'label')
                else:
                    out = os.path.join(root, k)
                if not os.path.exists(out):
                    os.makedirs(out)
                if k == 'text' or k == "label":
                    v_k = list(v.keys())
                    v_k.sort()
                    for i in v_k:
                        file = v[i]
                        if file.endswith('.json'):
                            with open(file, 'r', encoding="utf-8") as f:
                                json_info = json.load(f)
                                f.close()
                            if k == 'text':
                                text_data.append(json_info)
                            else:
                                label_data.append(json_info)
                    if k == 'text':
                        with open(os.path.join(out, name + '.json'), 'w', encoding="utf-8") as f:
                            f.write(json.dumps(text_data, ensure_ascii=False))
                            f.close()
                    else:
                        with open(os.path.join(out, name + '.json'), 'w', encoding="utf-8") as f:
                            f.write(json.dumps(label_data, ensure_ascii=False))
                            f.close()
                else:
                    file_name = os.path.basename(key)
                    out = os.path.join(out, file_name)
                    if not os.path.exists(out):
                        os.makedirs(out)
                    for file in v:
                        shutil.copy2(file, out)
            shutil.rmtree(key)