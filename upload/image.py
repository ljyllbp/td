from upload import *
from config import *
import shutil

class image_upload(upload):    
    def start_upload(self):
        try:
            self.check_data_root()
            self.add_order_sn_and_sequence_id()
            self.get_batch_sn()
        except Exception as e:
            raise_error(e, self.error_record_path)

        try:
            self.get_oss_config()
            self.add_oss_file_path()
            self.upload_files()
            self.change_path_original()
            self.call_back_success()
            self.log_fp.close()
            if self.debug:
                print(f"批次号: {self.batch_sn}")
            return self.batch_sn
        except Exception as e:
            self.call_back_fail(e)
            raise_error(e, self.error_record_path)

    # 检查预标注结果文件:id
    def pre_label_file_check(self, pre_label_file_path):
        with open(pre_label_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        object_ids = []

        # 获取id
        if "labels" in data:
            for index, obj in enumerate(data["labels"]):
                if "object_id" in obj:
                    object_id = obj["object_id"]
                    self.assert_id(object_id)
                    if object_id not in object_ids:
                        object_ids.append(object_id)
                    else:
                        raise Exception(f"object_id 重复 {object_id}")

        # 生成id
        id_index = 0
        if "labels" in data:
            for index, obj in enumerate(data["labels"]):
                if "object_id" not in obj:
                    object_id, id_index  = self.get_id_prelabel(id_index, object_ids)
                    id_index += 1
                    obj["object_id"] = object_id
                    object_ids.append(object_id)
        with open(pre_label_file_path, "w", encoding="utf-8") as f:
            data = json.dump(data,f,ensure_ascii=False,indent=4)

    # 校验img目录
    def check_img_root(self, segment_root):

        img_root = self.path_join(segment_root, "img")
        
        img_files_info = {}

        if not os.path.exists(img_root):
            if len(self.move_files[segment_root]) == 0:
                error_path = self.get_relative_path(img_root)
                raise Exception(f"expect error: {error_path} 目录下图像文件数为0")
            
            return img_files_info
            
        
        self.is_root(img_root)

        file_types = IMAGE_FILE_TYPES
        error_str = "不支持该类型图片文件"
        
        
        img_files_info = self.check_file_root(img_root, file_types, error_str)
        
        if len(self.move_files[segment_root]) == 0 and not img_files_info:
            error_path = self.get_relative_path(img_root)
            raise Exception(f"expect error: {error_path} 目录下图像文件数为0")
        
        for _, img_file_info in img_files_info.items():
            self.assert_illegal_characters(self.get_relative_path(img_file_info["file_path"]))
        for move_file in self.move_files[segment_root]:
            self.assert_illegal_characters(self.get_relative_path(move_file[0]))
        
        return img_files_info
    
    # 校验pre_label目录
    def check_pre_label_root(self, segment_root):

        pre_label_root = self.path_join(segment_root, "pre_label")
        
        if not os.path.exists(pre_label_root):
            return None

        self.is_root(pre_label_root)

        file_types = PRE_LABEL_FILE_TYPES
        error_str = "不支持该类型预标注文件"
        pre_label_files_info = self.check_file_root(pre_label_root, file_types, error_str)
        
        return pre_label_files_info

    # 对比图像,预标注结果
    def compare_images_pre_labels(self, img_files_info, pre_label_files_info, segment_root):

        for img_file_name, img_file_info in img_files_info.items():
            
            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                if img_file_name not in pre_label_files_info:
                    error_path = self.get_relative_path(img_file_info["file_path"])
                    raise Exception(f"expect error: {error_path} 未找到预标注结果文件")
                else:
                    try:
                        self.pre_label_file_check(pre_label_files_info[img_file_name]["file_path"])
                    except Exception as e:
                        error_path = self.get_relative_path(pre_label_files_info[img_file_name]["file_path"])
                        raise Exception(f"expect error: {error_path} 预标注结果文件检查出错 {str(e)}")
        
        for move_file_info in self.move_files[segment_root]:
            
            img_file_name = self.get_file_name(move_file_info[0])
            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                if img_file_name not in pre_label_files_info:
                    error_path = self.get_relative_path(move_file_info[0])
                    raise Exception(f"expect error: {error_path} 未找到预标注结果文件")
                else:
                    try:
                        self.pre_label_file_check(pre_label_files_info[img_file_name]["file_path"])
                    except Exception as e:
                        error_path = self.get_relative_path(pre_label_files_info[img_file_name]["file_path"])
                        raise Exception(f"expect error: {error_path} 预标注结果文件检查出错 {str(e)}")

    # 校验每一个序列并获取文件列表
    def check_segment_roots(self, segment_roots):
        segment_root_count = len(segment_roots)
        for index, segment_root in enumerate(segment_roots):
            
            debug_path = self.get_relative_path(segment_root)
            segment_root_index = index + 1
            data_type_zh = self.dsinfo["data_type_zh"]
            self.loged(f"{data_type_zh} 校验目录: {segment_root_index}/{segment_root_count} {debug_path}")
        
            img_files_info = self.check_img_root(segment_root)
            pre_label_files_info = self.check_pre_label_root(segment_root)
            
            self.compare_images_pre_labels(img_files_info, pre_label_files_info, segment_root)

            self.get_file_list(segment_root, img_files_info, pre_label_files_info)

    # 获取序列目录
    def get_segment_roots(self):
        segment_roots = []

        if os.path.isfile(self.data_root):
            error_path = self.get_relative_path(self.data_root)
            raise Exception(f"expect error: 错误文件:{error_path},应为目录")

        segment_roots.append(self.data_root)

        if len(segment_roots) == 0:
            raise Exception("expect error: 序列目录数量为0")

        segment_roots.sort()

        return segment_roots  

    # 移动非img目录图像文件
    def build_segment(self, segment_roots):
        for segment_root in segment_roots:
            self.move_files[segment_root] = []
            files = os.listdir(segment_root)
            for file in files:
                if file.endswith(IMAGE_FILE_TYPES) and not file.startswith("."):
                    file_path = self.path_join(segment_root, file)
                    if os.path.isfile(file_path):
                        file_tar_path = self.path_join(segment_root, "img", file)
                        if os.path.exists(file_tar_path):
                            error_path = self.get_relative_path(file_path)
                            error_path_ = self.get_relative_path(file_tar_path)
                            raise Exception(f"expect error: 同名文件:{error_path} {error_path_}")
                        self.move_files[segment_root].append(
                            [
                                file_path,
                                file_tar_path
                            ]
                        )

    # 校验文件夹
    def check_data_root(self):
        segment_roots = self.get_segment_roots()
        self.build_segment(segment_roots)
        self.check_segment_roots(segment_roots)

    # 获取上传文件列表
    def get_file_list(self, segment_root, img_files_info, pre_label_files_info):
        
        segment_relative_root = self.get_relative_path(segment_root)
        self.upload_files_path[segment_relative_root] = {}

        # 循环图像文件
        for img_file_name, img_file_info in img_files_info.items():
            
            img_file_path = img_file_info["file_path"]
            img_file_relative_path = self.get_relative_path(img_file_path)
            self.upload_files_path[segment_relative_root][img_file_relative_path] = self.get_file_info(img_file_path, True)
            self.upload_files_count += 1

            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                pre_label_file_path = pre_label_files_info[img_file_name]["file_path"]
                pre_label_file_relative_path = self.get_relative_path(pre_label_file_path)
                self.upload_files_path[segment_relative_root][pre_label_file_relative_path] = self.get_file_info(pre_label_file_path)
                self.upload_files_count += 1
        
        # 循环移动的图像文件
        for move_file_info in self.move_files[segment_root]:
            
            img_source_path = move_file_info[0]
            img_tar_path = move_file_info[1]
            img_tar_relative_path = self.get_relative_path(img_tar_path)
            self.upload_files_path[segment_relative_root][img_tar_relative_path] = self.get_file_info(img_source_path, True)
            self.upload_files_count += 1

            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                img_file_name = self.get_file_name(img_tar_path)
                pre_label_file_path = pre_label_files_info[img_file_name]["file_path"]
                pre_label_file_relative_path = self.get_relative_path(pre_label_file_path)
                self.upload_files_path[segment_relative_root][pre_label_file_relative_path] = self.get_file_info(pre_label_file_path)
                self.upload_files_count += 1