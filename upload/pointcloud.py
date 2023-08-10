from upload import *
from config import *
import json
import subprocess
from copy import deepcopy

class pointcloud_upload(upload):    
    def start_upload(self):
        
        try:
            self.check_data_root()
            self.segment_split()
            self.simplify_pcd()
            self.check_md5()
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
    
    def segment_split(self):
        
        if self.package_count is None:
            return
        if self.debug:
            print("分包")
        
        self.upload_files_count = 0

        new_upload_files_path = {}
        for segment_relative_root in self.upload_files_path.keys():
            segment_name = os.path.basename(segment_relative_root)
            files = {}
            config = []
            for file_relative_path in self.upload_files_path[segment_relative_root].keys():
                file_name = self.get_file_name(file_relative_path)
                file_type = self.get_file_type(file_relative_path)
                if file_name == "config" and file_type == "json" and os.path.dirname(file_relative_path) == segment_relative_root:
                    config = [
                        file_relative_path,
                        self.upload_files_path[segment_relative_root][file_relative_path]
                    ]
                else:
                    if file_name not in files:
                        files[file_name] = {
                            "lidar": [],
                            "camera": [],
                            "pre_label": []
                        }
                    if file_type in POINTCLOUD_FILE_TYPES:
                        files[file_name]["lidar"].append(file_relative_path)
                        files[file_name]["lidar"].append(self.upload_files_path[segment_relative_root][file_relative_path])
                    elif file_type in IMAGE_FILE_TYPES:
                        files[file_name]["camera"].append(file_relative_path)
                        files[file_name]["camera"].append(self.upload_files_path[segment_relative_root][file_relative_path])
                    else:
                        files[file_name]["pre_label"].append(file_relative_path)
                        files[file_name]["pre_label"].append(self.upload_files_path[segment_relative_root][file_relative_path])
            file_index = -1
            for file_name in sorted(files.keys()):
                file_index += 1
                new_segment_name = segment_name + PACKAGE_SPECIAL_STRING + str(file_index // self.package_count).rjust(5,"0")
                new_segment_relative_root = self.path_join(os.path.dirname(segment_relative_root), new_segment_name)

                if new_segment_relative_root not in new_upload_files_path:
                    new_upload_files_path[new_segment_relative_root] = {}
                    new_upload_files_path[new_segment_relative_root][config[0]] = deepcopy(config[1])
                    self.upload_files_count += 1

                for k, v in files[file_name].items():
                    for index, _ in enumerate(files[file_name][k]):
                        if index % 2 != 0:
                            continue
                        new_upload_files_path[new_segment_relative_root][files[file_name][k][index]] = files[file_name][k][index+1]
                        self.upload_files_count += 1

        self.upload_files_path = new_upload_files_path

    # 精简点云
    def simplify_pcd(self):
        if not self.is_simplify_pcd:
            return
        
        self.loged("精简点云")
        
        exe_head = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        if OS_TYPE == "mac_arm64":
            exe_path = f"{exe_head}/c/pcdCompressMacM1"
        elif OS_TYPE == "mac_amd64":
            exe_path = f"{exe_head}/c/pcdCompressMac"
        elif OS_TYPE == "win":
            exe_path = f"{exe_head}\c\pcdCompress.exe"
        elif OS_TYPE == "ubuntu":
            exe_path = f"{exe_head}/c/pcdCompressUbuntu"
        
        res_bin_path = f"{self.data_root}/.resbin"
        
        if os.path.exists(res_bin_path):
            os.remove(res_bin_path)

        if self.is_force_Compressed:
            if self.debug:
                if OS_TYPE != "win":
                    subprocess.check_call(f"{exe_path} '{self.data_root}' '{res_bin_path}' 1 1", shell=True)
                else:
                    subprocess.check_call(f"{exe_path} \"{self.data_root}\" \"{res_bin_path}\" 1 1", shell=True)
            else:
                if OS_TYPE != "win":
                    subprocess.check_call(f"{exe_path} '{self.data_root}' '{res_bin_path}' 1 0", shell=True)
                else:
                    subprocess.check_call(f"{exe_path} \"{self.data_root}\" \"{res_bin_path}\" 1 0", shell=True)
        else:
            if self.debug:
                if OS_TYPE != "win":
                    subprocess.check_call(f"{exe_path} '{self.data_root}' '{res_bin_path}' 0 1", shell=True)
                else:
                    subprocess.check_call(f"{exe_path} \"{self.data_root}\" \"{res_bin_path}\" 0 1", shell=True)
            else:
                if OS_TYPE != "win":
                    subprocess.check_call(f"{exe_path} '{self.data_root}' '{res_bin_path}' 0 0", shell=True)
                else:
                    subprocess.check_call(f"{exe_path} \"{self.data_root}\" \"{res_bin_path}\" 0 0")
                
        if os.path.exists(res_bin_path):
            os.remove(res_bin_path)
        else:
            raise Exception("expect error: 点云文件精简失败")
        
        segment_count = len(self.upload_files_path.keys())
        segment_index = 0
        for segment_relative_root in self.upload_files_path.keys():
            segment_index += 1
            self.loged(f"重新获取序列信息: {segment_index}/{segment_count} {segment_relative_root}")
            for file_relative_path in self.upload_files_path[segment_relative_root].keys():
                if not file_relative_path.endswith((POINTCLOUD_FILE_TYPES)):
                    continue
                pcd_file_path = self.upload_files_path[segment_relative_root][file_relative_path]["path_original"]
                self.upload_files_path[segment_relative_root][file_relative_path]["path_original"] = self.get_new_pcd_file_path(pcd_file_path)
                self.upload_files_path[segment_relative_root][file_relative_path]["size"] = self.get_file_size(self.upload_files_path[segment_relative_root][file_relative_path]["path_original"])
                self.upload_files_path[segment_relative_root][file_relative_path]["md5"] = self.get_file_md5(self.upload_files_path[segment_relative_root][file_relative_path]["path_original"])

    # 检查预标注结果文件:id
    def pre_label_file_check(self, pre_label_file_file_path):
        with open(pre_label_file_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ids = []

        # 获取id
        if "lidar" in data:
            for index, lidar_obj in enumerate(data["lidar"]):
                if "id" in lidar_obj:
                    id = lidar_obj["id"]
                    self.assert_id(id)
                    if id not in ids:
                        ids.append(id)
                    else:
                        raise Exception(f"id 重复 {id}")
        if "camera" in data:
            for cam_name, cam_objs in data["camera"].items():
                for index, cam_obj in enumerate(cam_objs):
                    if "id" in cam_obj:
                        id = cam_obj["id"]
                        self.assert_id(id)
                        if id not in ids:
                            ids.append(id)
                        else:
                            raise Exception(f"id 重复 {id}")

        # 生成id
        id_index = 0
        if "lidar" in data:
            for index, lidar_obj in enumerate(data["lidar"]):
                if "id" not in lidar_obj:
                    id, id_index  = self.get_id_prelabel(id_index, ids)
                    id_index += 1
                    lidar_obj["id"] = id
                    ids.append(id)
        
        if "camera" in data:
            for cam_name, cam_objs in data["camera"].items():
                for index, cam_obj in enumerate(cam_objs):
                    if "id" not in cam_obj:
                        id, id_index  = self.get_id_prelabel(id_index, ids)
                        id_index += 1
                        cam_obj["id"] = id
                        ids.append(id)
        
        with open(pre_label_file_file_path, "w", encoding="utf-8") as f:
            data = json.dump(data,f,ensure_ascii=False,indent=4)

    # 校验参数
    def check_sensor_param(self, sensor_param):
        is_error = False
        error_str = None
        
        if not isinstance(sensor_param,dict):
            is_error = True
            error_str = "融合参数数据类型应为字典"
            return is_error, error_str
        
        if "camera_model" not in sensor_param:
            is_error = True
            error_str = "camera_model字段缺少"
            return is_error, error_str
        else:
            if not isinstance(sensor_param["camera_model"], str):
                is_error = True
                error_str = "camera_model字段类型应为字符串"
                return is_error, error_str
        
        camera_model = sensor_param["camera_model"]

        sensor_params_struct = SENSOR_PARAMS_STRUCT

        if camera_model not in sensor_params_struct:
            is_error = True
            error_str = "camera_model 值错误"
            return is_error, error_str

        # 可选字段校验
        for field_name, field_info in sensor_params_struct[camera_model]["optional"].items():
            if field_name in sensor_param:
                if not isinstance(sensor_param[field_name], field_info["type"]):
                    is_error = True
                    error_str = field_info["error_str"]
                    return is_error, error_str
        
        # 必须字段校验
        for field_name, field_info in sensor_params_struct[camera_model]["necessary"].items():
            if field_name not in sensor_param:
                is_error = True
                error_str = f"缺少字段{field_name}"
                return is_error, error_str
            
            if field_name == "extrinsic":
                extrinsic_error_flag = False
                try:
                    if len(sensor_param[field_name]) != 4:
                        extrinsic_error_flag =True
                    for row in range(4):
                        if len(sensor_param[field_name][row]) != 4:
                            extrinsic_error_flag =True
                        for col in range(4):
                            if not isinstance(sensor_param[field_name][row][col],(float, int)):
                                extrinsic_error_flag =True
                except :
                    is_error = True
                    error_str = field_info["error_str"]
                    return is_error, error_str
                if extrinsic_error_flag == True:
                    is_error = True
                    error_str = field_info["error_str"]
                    return is_error, error_str
            elif field_name == "affine_params":
                try:
                    assert(isinstance(sensor_param[field_name]["ac"], (float, int)))
                    assert(isinstance(sensor_param[field_name]["ad"], (float, int)))
                    assert(isinstance(sensor_param[field_name]["ae"], (float, int)))
                    assert(isinstance(sensor_param[field_name]["cx"], (float, int)))
                    assert(isinstance(sensor_param[field_name]["cy"], (float, int)))
                except :
                    is_error = True
                    error_str = field_info["error_str"]
                    return is_error, error_str
            elif field_name == "inv_poly_params":
                try:
                    assert(isinstance(sensor_param[field_name], list))
                    assert((len(sensor_param[field_name]) == 10 or len(sensor_param[field_name]) == 20))
                    for num in sensor_param[field_name]:
                        assert(isinstance(num, (int, float)))
                except :
                    is_error = True
                    error_str = field_info["error_str"]
                    return is_error, error_str
            else:
                if not isinstance(sensor_param[field_name], field_info["type"]):
                    is_error = True
                    error_str = field_info["error_str"]
                    return is_error, error_str
            
        return is_error, error_str

    # 校验lidar目录
    def check_lidar_root(self, segment_root):

        lidar_root = self.path_join(segment_root, "lidar")
        
        if not os.path.exists(lidar_root):
            error_path = self.get_relative_path(lidar_root)
            raise Exception(f"expect error: {error_path} 不存在")
        self.is_root(lidar_root)

        file_types = POINTCLOUD_FILE_TYPES
        error_str = "不支持该类型点云文件"
        pcd_files_info = self.check_file_root(lidar_root, file_types, error_str)
        
        if not pcd_files_info:
            error_path = self.get_relative_path(lidar_root)
            raise Exception(f"expect error: {error_path} 目录下点云文件数为0")
        
        # 校验特殊字符
        for _, pcd_file_info in pcd_files_info.items():
            self.assert_illegal_characters(self.get_relative_path(pcd_file_info["file_path"]))
        
        return pcd_files_info
    
    # 校验camera目录
    def check_camera_root(self, segment_root):
        
        camera_image_dict = {}

        camera_root = self.path_join(segment_root, "camera")
        
        if not os.path.exists(camera_root):
            return camera_image_dict
        self.is_root(camera_root)
        
        camera_names_ = os.listdir(camera_root)
        for camera_name in camera_names_:
            
            if self.ignore(camera_name):
                continue

            image_root = self.path_join(camera_root, camera_name)
            file_types = IMAGE_FILE_TYPES
            error_str = "不支持该类型图片文件"
            image_files_info = self.check_file_root(image_root, file_types, error_str)
            
            camera_image_dict[camera_name] = image_files_info
        
        return camera_image_dict
    
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

    # 对比点云,图像,预标注结果
    def compare_pcds_images_pre_labels(self, pcd_files_info, camare_images_dict, pre_label_files_info):

        for pcd_file_name, pcd_file_info in pcd_files_info.items():
            
            # self.upload_files_path.append(pcd_file_info["file_path"])

            # 相机目录
            for camera_name, image_files_info in camare_images_dict.items():
                # 每一个相机目录
                if pcd_file_name not in image_files_info:
                    error_path = self.get_relative_path(pcd_file_info["file_path"])
                    raise Exception(f"expect error: {error_path} {camera_name}视角下未找到图像文件")
            
                # self.upload_files_path.append(image_files_info[pcd_file_name]["file_path"])

            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                if pcd_file_name not in pre_label_files_info:
                    error_path = self.get_relative_path(pcd_file_info["file_path"])
                    raise Exception(f"expect error: {error_path} 未找到预标注结果文件")
                else:
                    try:
                        self.pre_label_file_check(pre_label_files_info[pcd_file_name]["file_path"])
                    except Exception as e:
                        error_path = self.get_relative_path(pre_label_files_info[pcd_file_name]["file_path"])
                        raise Exception(f"expect error: {error_path} 预标注结果文件检查出错 {str(e)}")

                # self.upload_files_path.append(pre_label_files_info[pcd_file_name]["file_path"])                
            
    def check_range(self, range_):
        is_error = True
        error_str = None
        if not isinstance(range_, dict):
            is_error = False
            error_str = "range 信息为字典类型"
                
        for range_type, infos in range_.items():
            if range_type not in RANGE:
                error_str = f"暂不支持 range 类型: {range_type}"
                return is_error, error_str
            
            if not isinstance(infos, list):
                error_str = f"{range_type} 应为列表"
                return is_error, error_str

            range_dict = RANGE[range_type]
            for index, info in enumerate(infos):
                index_ = index + 1

                if not isinstance(info, dict):
                    error_str = f"{range_type} 第{index_}个标注范围 应为字典"
                    return is_error, error_str

                for k, v in range_dict.items():
                    if k not in info:
                        error_str = f"{range_type} 第{index_}个标注范围 缺少{k}字段"
                        return is_error, error_str
                    try:
                        assert(isinstance(info[k],v["type"]))
                        if isinstance(info[k],list):
                            assert(len(info[k]) == v["len"])
                            for i in info[k]:
                                assert(isinstance(i, v["mem_type"]))
                    except Exception as e:
                        error_str_ = v["error_str"]
                        error_str = f"{range_type} 第{index_}个标注范围 {error_str_}"
                        return is_error, error_str
        return False, error_str

    # 校验以及修正config文件
    def check_config_flie(self, segment_root, pcd_files_info, camare_images_dict):
        config_path = self.path_join(segment_root,"config.json")
        error_path = self.get_relative_path(config_path)
        
        # 不存在config文件
        if not os.path.exists(config_path):
            # 构造config文件
            config = {
                "data_type": POINTCLOUD,
            }
            # for camera_name, _ in camare_images_dict.items():
            #     if "camera" not in config:
            #         config["camera"] = {}
            #     config["camera"][camera_name] = camera_name
            config["camera"] = {}
            for camera_name in sorted(camare_images_dict.keys()):
                config["camera"][camera_name] = camera_name
            # 写config文件
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return
        
        # 存在config文件
        self.is_file(config_path)
        
        # cofig文件是否加载成功
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            raise Exception(f"expect error: {error_path} 加载config文件出错")
        
        # config为字典格式
        if not isinstance(config, dict):
            raise Exception(f"expect error: {error_path} 格式错误,json内容应为字典")
        
        # 校验camera
        if "camera" not in config:
            # for camera_name, _ in camare_images_dict.items():
            #     if "camera" not in config:
            #         config["camera"] = {}
            #     config["camera"][camera_name] = camera_name
            config["camera"] = {}
            for camera_name in sorted(camare_images_dict.keys()):
                config["camera"][camera_name] = camera_name
        else:
            if not isinstance(config["camera"], dict):
                raise Exception(f"expect error: {error_path} 中camera对应值应为字典")

            for camera_name, _ in camare_images_dict.items():
                if camera_name not in config["camera"]:
                    config["camera"][camera_name] = camera_name
                else:
                    if not isinstance(config["camera"][camera_name], str):
                        raise Exception(f"expect error: {error_path} 中camera下{camera_name}对应数据类型应为字符串")
            for camera_name, _ in config["camera"].items():
                if camera_name not in camare_images_dict:
                    raise Exception(f"expect error: {error_path} 中camera下{camera_name}相机不应该存在")

        # 校验 data_type
        if "data_type" not in config:
            raise Exception(f"expect error: {error_path} data_type字段缺少")
        else:
            if not isinstance(config["data_type"], str):
                raise Exception(f"expect error: {error_path} data_type应为字符串")
            if config["data_type"] not in POINTCLOUD_TYPE:
                raise Exception(f"expect error: {error_path} data_type值错误")
        
        # 校验融合参数

        if config["data_type"] != POINTCLOUD:
            if "sensor_params" not in config:
                raise Exception(f"expect error: {error_path} sensor_params字段缺少")
            sensor_params = config["sensor_params"]
            if not isinstance(sensor_params,dict):
                raise Exception(f"expect error: {error_path} sensor_params应为字典")

        # 融合点云 FUSION_POINTCLOUD
        if config["data_type"] == FUSION_POINTCLOUD:
            for camera_name, _ in camare_images_dict.items():
                if camera_name not in sensor_params:
                    raise Exception(f"expect error: {error_path} sensor_params下缺少相机{camera_name}的融合参数")
                sensor_param = sensor_params[camera_name]
                is_error, error_str = self.check_sensor_param(sensor_param)
                if is_error:
                    raise Exception(f"expect error: {error_path} sensor_params下相机{camera_name} {error_str}")
                
        # 单帧融合点云 SINGLE_FUSION_POINTCLOUD
        elif config["data_type"] == SINGLE_FUSION_POINTCLOUD:
            for pcd_file_name, _ in pcd_files_info.items():
                if pcd_file_name not in sensor_params:
                    raise Exception(f"expect error: {error_path} 点云文件:{pcd_file_name} 缺少对应参数")
                if not isinstance(sensor_params[pcd_file_name], dict):
                    raise Exception(f"expect error: {error_path} 点云文件:{pcd_file_name} 参数应为字典类型")
                
                for camera_name, _ in camare_images_dict.items():
                    if camera_name not in sensor_params[pcd_file_name]:
                        raise Exception(f"expect error: {error_path} 点云文件{pcd_file_name}缺少相机{camera_name}的融合参数")
                    sensor_param = sensor_params[pcd_file_name][camera_name]
                    is_error, error_str = self.check_sensor_param(sensor_param)
                    if is_error:
                        raise Exception(f"expect error: {error_path} sensor_params 点云文件{pcd_file_name} 相机{camera_name} {error_str}")
        
        # 校验pose信息
        if "poses" in config:
            if not isinstance(config["poses"], dict):
                raise Exception(f"expect error: {error_path} poses 信息为字典类型")
            for pcd_file_name, _ in pcd_files_info.items():
                if pcd_file_name not in config["poses"]:
                    raise Exception(f"expect error: {error_path} 点云文件:{pcd_file_name} 缺少pose参数")
                try:
                    assert(isinstance(config["poses"][pcd_file_name], list))
                    for i in range(16):
                        assert(isinstance(config["poses"][pcd_file_name][i],(float, int)))
                except:
                    raise Exception(f"expect error: {error_path} 点云文件:{pcd_file_name} pose参数错误 应为16位float的list")

        # 校验标注范围信息
        if "range" in config:
            range_ = config["range"]
            is_error, error_str = self.check_range(range_)
            if is_error:
                raise Exception(f"expect error: {error_path} range {error_str}")
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    # 校验每一个序列并获取文件列表
    def check_segment_roots(self, segment_roots):
        segment_root_count = len(segment_roots)
        for index, segment_root in enumerate(segment_roots):
            
            debug_path = self.get_relative_path(segment_root)
            segment_root_index = index + 1
            data_type_zh = self.dsinfo["data_type_zh"]
            self.loged(f"{data_type_zh} 校验目录: {segment_root_index}/{segment_root_count} {debug_path}")
            
            pcd_files_info = self.check_lidar_root(segment_root)
            camare_images_dict = self.check_camera_root(segment_root)
            pre_label_files_info = self.check_pre_label_root(segment_root)
            
            self.compare_pcds_images_pre_labels(pcd_files_info, camare_images_dict, pre_label_files_info)
            self.check_config_flie(segment_root, pcd_files_info, camare_images_dict)

            self.get_file_list(segment_root, pcd_files_info, camare_images_dict, pre_label_files_info)
  

    # 校验文件夹
    def check_data_root(self):
        segment_roots = self.get_segment_roots()

        self.check_segment_roots(segment_roots)
    
    # 获取点云文件路径
    def get_new_pcd_file_path(self, pcd_file_path):
        if not self.is_simplify_pcd:
            return pcd_file_path
        else:
            pcd_file = os.path.basename(pcd_file_path)
            segment_name = os.path.basename(os.path.dirname(os.path.dirname(pcd_file_path)))
            new_pcd_file_path = self.path_join(self.data_root, PCD_S_ROOT, segment_name, "lidar",pcd_file)
            if os.path.exists(new_pcd_file_path):
                return new_pcd_file_path
            else:
                return pcd_file_path

    # 获取上传文件列表
    def get_file_list(self, segment_root, pcd_files_info, camare_images_dict, pre_label_files_info):
        
        segment_relative_root = self.get_relative_path(segment_root)
        self.upload_files_path[segment_relative_root] = {}
        
        # 添加config文件
        config_path = self.path_join(segment_root, "config.json")
        config_relative_path = self.get_relative_path(config_path)
        self.upload_files_path[segment_relative_root][config_relative_path] = self.get_file_info(config_path)
        self.upload_files_count += 1

        # 循环点云文件
        for pcd_file_name, pcd_file_info in pcd_files_info.items():
            
            pcd_file_path = pcd_file_info["file_path"]
            pcd_file_relative_path = self.get_relative_path(pcd_file_path)
            self.upload_files_path[segment_relative_root][pcd_file_relative_path] = self.get_file_info(pcd_file_path, size_md5=not(self.is_simplify_pcd))
            self.upload_files_count += 1

            # 相机目录
            for camera_name, image_files_info in camare_images_dict.items():
                # 每一个相机目录                
                image_file_path = image_files_info[pcd_file_name]["file_path"]
                image_file_relative_path = self.get_relative_path(image_file_path)
                self.upload_files_path[segment_relative_root][image_file_relative_path] = self.get_file_info(image_file_path,True)
                self.upload_files_count += 1

            # 预标注目录
            if isinstance(pre_label_files_info, dict):
                pre_label_file_path = pre_label_files_info[pcd_file_name]["file_path"]
                pre_label_file_relative_path = self.get_relative_path(pre_label_file_path)
                self.upload_files_path[segment_relative_root][pre_label_file_relative_path] = self.get_file_info(pre_label_file_path)
                self.upload_files_count += 1