from upload import *
from config import *
import shutil

class image_upload(upload):    
    def start_upload(self):
        try:
            self.delete_add_files()
            self.check_data_root()
            self.add_order_sn_and_sequence_id()
        except Exception as e:
            self.save_add_files()
            self.delete_add_files()
            raise Exception(str(e))

        try:
            self.get_batch_sn()
            self.get_oss_config()
            # self.get_id()

            self.add_oss_file_path()
            self.upload_files()
            self.call_back_success()
            if self.debug:
                print(f"batch_sn: {self.batch_sn}")
            return self.batch_sn
        except Exception as e:
            self.call_back_fail(e)
            raise Exception(str(e))
        finally:
            self.save_add_files()
            self.delete_add_files()

    # 校验img目录
    def check_img_root(self, segment_root):

        img_root = os.path.join(segment_root, "img")
        
        if not os.path.exists(img_root):
            error_path = self.get_relative_path(img_root)
            raise Exception(f"{error_path} 不存在")
        
        self.is_root(img_root)

        file_types = IMAGE_FILE_TYPES
        error_str = "不支持该类型图像文件"
        img_files_info = self.check_file_root(img_root, file_types, error_str)
        
        if not img_files_info:
            error_path = self.get_relative_path(img_root)
            raise Exception(f"{error_path} 目录下图像文件数为0")
        
        return img_files_info
    
    # 校验pre_label目录
    def check_pre_label_root(self, segment_root):

        pre_label_root = os.path.join(segment_root, "pre_label")
        
        if not os.path.exists(pre_label_root):
            return None

        self.is_root(pre_label_root)

        file_types = PRE_LABEL_FILE_TYPES
        error_str = "不支持该类型预标注文件"
        pre_label_files_info = self.check_file_root(pre_label_root, file_types, error_str)
        
        return pre_label_files_info

    # 对比图像,预标注结果
    def compare_images_pre_labels(self, img_files_info, pre_label_files_info):

        for img_file_name, img_file_info in img_files_info.items():
            
            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                if img_file_name not in pre_label_files_info:
                    error_path = self.get_relative_path(img_file_info["file_path"])
                    raise Exception(f"{error_path} 未找到预标注结果文件")

                # self.upload_files_path.append(pre_label_files_info[pcd_file_name]["file_path"])                

    # 校验每一个序列并获取文件列表
    def check_segment_roots(self, segment_roots):
        segment_root_count = len(segment_roots)
        for index, segment_root in enumerate(segment_roots):
            
            if self.debug:
                debug_path = self.get_relative_path(segment_root)
                segment_root_index = index + 1
                print(f"校验目录: {segment_root_index}/{segment_root_count} {debug_path}")
            
            img_files_info = self.check_img_root(segment_root)
            pre_label_files_info = self.check_pre_label_root(segment_root)
            
            self.compare_images_pre_labels(img_files_info, pre_label_files_info)

            self.get_file_list(segment_root, img_files_info, pre_label_files_info)

    # 获取序列目录
    def get_segment_roots(self):
        segment_roots = []

        if os.path.isfile(self.data_root):
            error_path = self.get_relative_path(self.data_root)
            raise Exception(f"错误文件:{error_path},应为目录")

        segment_roots.append(self.data_root)

        if len(segment_roots) == 0:
            raise Exception("序列目录数量为0")

        segment_roots.sort()

        return segment_roots  

    # 移动非img目录图像文件
    def build_segment(self, segment_roots):
        for segment_root in segment_roots:
            files = os.listdir(segment_root)
            for file in files:
                if file.endswith(IMAGE_FILE_TYPES) and not file.startswith("."):
                    file_path = os.path.join(segment_root, file)
                    if os.path.isfile(file_path):
                        img_root = os.path.join(segment_root, "img")
                        if not os.path.exists(img_root):
                            self.add_files_path.append(img_root)
                            os.makedirs(img_root)
                        file_tar_path = os.path.join(segment_root, "img", file)
                        if os.path.exists(file_tar_path):
                            error_path = self.get_relative_path(file_path)
                            error_path_ = self.get_relative_path(file_tar_path)
                            raise Exception(f"同名文件:{error_path} {error_path_}")
                        self.add_files_path.append(file_tar_path)
                        shutil.copy2(file_path, file_tar_path)

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