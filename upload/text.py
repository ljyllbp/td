from upload import *
from config import *
from xml.sax.saxutils import escape

class text_upload(upload):    
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

            self.add_oss_file_path()
            self.upload_files()
            self.change_path_original()
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

    # 获取云存储路径
    def add_oss_file_path(self):
        if self.debug:
            print("获取云存储路径")
        for segment_relative_root in self.upload_files_path.keys():
            for file_relative_path in self.upload_files_path[
                segment_relative_root
            ].keys():
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

    # 校验text目录
    def check_text_root(self, segment_root):

        text_root = os.path.join(segment_root, "text")
        
        if not os.path.exists(text_root):
            error_path = self.get_relative_path(text_root)
            raise Exception(f"{error_path} 不存在")
        
        self.is_root(text_root)

        file_types = TEXT_FILE_TYPES
        files_ = os.listdir(text_root)

        for file in files_:

            if self.ignore(file):
                continue
        
            file_path = os.path.join(text_root, file)

            self.is_file(file_path)

            file_type = self.get_file_type(file_path)
            if file_type not in file_types:
                error_path = self.get_relative_path(file_path)
                raise Exception(f"{error_path} 不支持该类型文本文件")

            self.assert_illegal_characters(self.get_relative_path(file_path))

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_data = json.load(f)
            except:
                error_path = self.get_relative_path(file_path)
                raise Exception(f"{error_path}, 文件读取错误")

            data_count = 0

            error_path = self.get_relative_path(file_path)

            if not isinstance(text_data, list):
                raise Exception(f"{error_path}, json内容应为list")
            
            for data_index, value in enumerate(text_data):
                data_count += 1
                if not isinstance(value,dict):
                    raise Exception(f"{error_path}, 第 {data_index} 条数据应为字典")
                # text
                if "text" not in value:
                    raise Exception(f"{error_path}, 第 {data_index} 条数据缺少字段text")
                else:
                    if not isinstance(value["text"], str):
                        raise Exception(f"{error_path}, 第 {data_index} 条数据text类型应为字符串")
                # pre_label
                if "pre_label" in value and not isinstance(value["pre_label"], dict):
                    raise Exception(f"{error_path}, 第 {data_index} 条数据pre_label类型应为字典")
                # img
                if "img" in value:
                    if not isinstance(value["img"], list):
                        raise Exception(f"{error_path}, 第 {data_index} 条数据img类型应为列表")
                    else:
                        text_name = self.get_file_name(file_path)
                        for pic_index, pic_name in enumerate(value["img"]):
                            if not isinstance(pic_name,str):
                                raise Exception(f"{error_path}, 第{data_index}条数据img中应为字典")
                            else:
                                pic_path = os.path.join(segment_root, "img", text_name, pic_name)
                                if not os.path.exists(pic_path):
                                    pic_error_path = self.get_relative_path(pic_path)
                                    raise Exception(f"{error_path}, 第 {data_index} 条数据img第 {pic_index} 张图像 {pic_error_path} 缺少")
                                self.assert_illegal_characters(self.get_relative_path(pic_path))
                                pic_file_type = self.get_file_type(pic_path)
                                if pic_file_type not in IMAGE_FILE_TYPES:
                                    pic_error_path = self.get_relative_path(pic_path)
                                    raise Exception(f"{error_path}, 不支持该类型图像")

    # 对文本内容进行处理
    def text_content_deal(self, textcontent):
        # 替换tab
        textcontent = textcontent.replace(u"\u0009", u"\u3000")
        # 替换半角空格
        textcontent = textcontent.replace(u"\u0020", u"\u3000")
        # 替换emoji表情,unicode编码长度超过六就处理
        textcontent_new = ""
        for word in textcontent:
            if len(str(word.encode("unicode_escape"))) > 10:
                textcontent_new += u"\u3000"
            else:
                textcontent_new += word
        # 替换"零分割符"
        textcontent_new = textcontent_new.replace(u"\u200d", u"\u3000")
        # 替换\n
        textcontent_new = textcontent_new.replace("\n", u"\u3000")
        # 替换\t
        textcontent_new = textcontent_new.replace("\t", u"\u3000")
        # html转译
        textcontent_new = escape(textcontent_new)
        
        return textcontent_new


    # 构造目录并获取文件列表
    def struct_text_root(self, segment_root):
        segment_relative_root = self.get_relative_path(segment_root)
        self.upload_files_path[segment_relative_root] = {}
        text_root = os.path.join(segment_root, "text")
        files_ = os.listdir(text_root)

        for file in files_:

            if self.ignore(file):
                continue
    
            file_path = os.path.join(text_root, file)
            file_name = self.get_file_name(file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                text_data = json.load(f)

            for data_index, value in enumerate(text_data):
                # 原始数据
                text_content = {
                    "text": self.text_content_deal(value["text"])
                }
                if "img" in value:
                    text_content["img"] = value["img"]
                    # 将img添加到列表
                    for img_file in value["img"]:
                        source_img_file_path = os.path.join(segment_root, "img", file_name, img_file)
                        tar_img_file_path = os.path.join(segment_root,file_name,"img",str(data_index).rjust(5, "0"),img_file)
                        tar_img_file_relative_path = self.get_relative_path(tar_img_file_path)
                        self.upload_files_path[segment_relative_root][tar_img_file_relative_path] = self.get_file_info(source_img_file_path, True)
                        self.upload_files_path[segment_relative_root][tar_img_file_relative_path]["path_original"] = source_img_file_path
                        self.upload_files_count += 1

                text_content_save_path = os.path.join(segment_root,"text",file_name,"text",str(data_index).rjust(5, "0") + ".json")
                self.add_files_path.append(os.path.join(segment_root,"text",file_name))
                self.make_dir(text_content_save_path)
                with open(text_content_save_path, "w", encoding="utf-8") as f:
                    json.dump(text_content, f, ensure_ascii=False, indent=4)
                
                # 将text添加到列表
                text_content_save_path_ = os.path.join(segment_root,file_name,"text",str(data_index).rjust(5, "0") + ".json")
                text_content_save_relative_path_ = self.get_relative_path(text_content_save_path_)
                self.upload_files_path[segment_relative_root][text_content_save_relative_path_] = self.get_file_info(text_content_save_path)
                self.upload_files_path[segment_relative_root][text_content_save_relative_path_]["path_original"] = text_content_save_path
                self.upload_files_count += 1
                
                # raise Exception("111")
                # 预标注结果
                if "pre_label" not in value:
                    continue
                pre_label_content_save_path = os.path.join(segment_root,"text",file_name,"pre_label",str(data_index).rjust(5, "0") + ".json")
                self.make_dir(pre_label_content_save_path)
                with open(pre_label_content_save_path, "w", encoding="utf-8") as f:
                    json.dump(value["pre_label"], f, ensure_ascii=False, indent=4)
                
                # 将pre_label添加到列表
                pre_label_content_save_path_ = os.path.join(segment_root,file_name,"pre_label",str(data_index).rjust(5, "0") + ".json")
                pre_label_content_save_relative_path_ = self.get_relative_path(pre_label_content_save_path_)
                self.upload_files_path[segment_relative_root][pre_label_content_save_relative_path_] = self.get_file_info(pre_label_content_save_path)
                self.upload_files_path[segment_relative_root][pre_label_content_save_relative_path_]["path_original"] = pre_label_content_save_path
                self.upload_files_count += 1
                

    # 校验每一个序列并获取文件列表
    def check_segment_roots(self, segment_roots):
        segment_root_count = len(segment_roots)
        for index, segment_root in enumerate(segment_roots):
            
            if self.debug:
                debug_path = self.get_relative_path(segment_root)
                segment_root_index = index + 1
                print(f"校验目录: {segment_root_index}/{segment_root_count} {debug_path}")
            
            self.check_text_root(segment_root)
            self.struct_text_root(segment_root)

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

    # 校验文件夹
    def check_data_root(self):
        segment_roots = self.get_segment_roots()
        self.check_segment_roots(segment_roots)