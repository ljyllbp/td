

POINTCLOUD_FILE_TYPES = ("pcd") # 点云文件类型
IMAGE_FILE_TYPES = ("jpg","png","jpeg","bmp","webp","ico") # 图片文件类型
AUDIO_FILE_TYPES = ("wav", "mp3", "ogg") # 音频文件类型
VIDEO_FILE_TYPES = ("mp4", "webm", "ogg") # 视频文件类型
TEXT_FILE_TYPES = ("json") # 文本文件类型
PRE_LABEL_FILE_TYPES = ("json") # 预标注结果文件类型

ILLEGAL_CHARACTER = ("?", "#", ":", "%")

POINTCLOUD = "pointcloud" # 普通点云
FUSION_POINTCLOUD = "fusion_pointcloud" # 融合点云
SINGLE_FUSION_POINTCLOUD = "single_fusion_pointcloud" # 单帧融合点云
POINTCLOUD_TYPE = (POINTCLOUD, FUSION_POINTCLOUD, SINGLE_FUSION_POINTCLOUD)

OS_TYPES = ("mac_arm64", "mac_amd64", "win", "ubuntu")
OS_TYPE = "mac_arm64"

TD_NAME = "td"
TD_VERSION = "1.0.1"

BUCKET = "default"

PACKAGE_SPECIAL_STRING = "__TDPACKAGE__"
PCD_S_ROOT = ".TD_PCD_FILES"
TEXT_SPLIT_ROOT = ".TD_TEXT"

CALL_BACK_SUCCESS_COUNT = 5000
CHECK_MD5_COUNT = 500

MAX_THREAD_NUM = 20
MAX_RETRY_COUNT = 20

ALI_OSS_MULTIPART_THRESHOLD = 50 * 1024 * 1024
ALI_OSS_PART_SIZE = 10 * 1024 * 1024
ALI_OSS_NUM_THREADS = 2

DEV_AK = ""
DEV_HOST = "http://10.32.22.250"

TEST_AK = ""
TEST_HOST = "http://label-std-test.testin.cn"

PRIVATE_AK = ""
PRIVATE_HOST = ""

PRODUCTION_AK = ""
PRODUCTION_HOST = "http://label-std.testin.cn"

RANGE = {
    "circle": {
        "name": {
            "type": (str),
            "error_str": "name 应为字符串类型"
        },
        "radius": {
            "type": (int, float),
            "error_str": "radius 应为整型或浮点型"
        },
        "center": {
            "type": (list),
            "len": 3,
            "mem_type": (float, int),
            "error_str": "center 应为长度为3，类型为整型或浮点型的列表"
        }
    },
    "arc": {
        "name": {
            "type": (str),
            "error_str": "name 应为字符串类型"
        },
        "start": {
            "type": (int, float),
            "error_str": "start 应为整型或浮点型"
        },
        "end": {
            "type": (int, float),
            "error_str": "end 应为整型或浮点型"
        },
        "radius": {
            "type": (int, float),
            "error_str": "radius 应为整型或浮点型"
        },
        "center": {
            "type": (list),
            "len": 3,
            "mem_type": (float, int),
            "error_str": "center 长度为3，类型为整型或浮点型的列表"
        }
    },
    "rect": {
        "name": {
            "type": (str),
            "error_str": "name 应为字符串类型"
        },
        "x": {
            "type": (list),
            "len": 2,
            "mem_type": (float, int),
            "error_str": "x 长度为2，类型为整型或浮点型的列表"
        },
        "y": {
            "type": (list),
            "len": 2,
            "mem_type": (float, int),
            "error_str": "y 长度为2，类型为整型或浮点型的列表"
        }
    },
    "box": {
        "name": {
            "type": (str),
            "error_str": "name 应为字符串类型"
        },
        "x": {
            "type": (list),
            "len": 2,
            "mem_type": (float, int),
            "error_str": "x 长度为2，类型为整型或浮点型的列表"
        },
        "y": {
            "type": (list),
            "len": 2,
            "mem_type": (float, int),
            "error_str": "x 长度为2，类型为整型或浮点型的列表"
        },
         "z": {
            "type": (list),
            "len": 2,
            "mem_type": (float, int),
            "error_str": "z 长度为2，类型为整型或浮点型的列表"
        }
    }
}

SENSOR_PARAMS_STRUCT = {
    "pinhole":{
        "optional":{
            "fov":{
                "type": (float, int),
                "error_str": "fov数据类型应为整型或浮点型"
            },
            "camera_euler_z":{
                "type": (float, int),
                "error_str": "camera_euler_z数据类型应为整型或浮点型"
            }
        },
        "necessary":{
            "fx":{
                "type": (float, int),
                "error_str": "fx数据类型应为整型或浮点型"
            },
            "fy":{
                "type": (float, int),
                "error_str": "fy数据类型应为整型或浮点型"
            },
            "cx":{
                "type": (float, int),
                "error_str": "cx数据类型应为整型或浮点型"
            },
            "cy":{
                "type": (float, int),
                "error_str": "cy数据类型应为整型或浮点型"
            },
            "k1":{
                "type": (float, int),
                "error_str": "k1数据类型应为整型或浮点型"
            },
            "k2":{
                "type": (float, int),
                "error_str": "k2数据类型应为整型或浮点型"
            },
            "k3":{
                "type": (float, int),
                "error_str": "k3数据类型应为整型或浮点型"
            },
            "p1":{
                "type": (float, int),
                "error_str": "p1数据类型应为整型或浮点型"
            },
            "p2":{
                "type": (float, int),
                "error_str": "p2数据类型应为整型或浮点型"
            },
            "extrinsic":{
                "type": "4*4 list float or int",
                "error_str": "extrinsic数据类型应为4*4的浮点型或整型的列表"
            }
        }
    },
    "pinhole1":{
        "optional":{
            "fov":{
                "type": (float, int),
                "error_str": "fov数据类型应为整型或浮点型"
            },
            "camera_euler_z":{
                "type": (float, int),
                "error_str": "camera_euler_z数据类型应为整型或浮点型"
            }
        },
        "necessary":{
            "fx":{
                "type": (float, int),
                "error_str": "fx数据类型应为整型或浮点型"
            },
            "fy":{
                "type": (float, int),
                "error_str": "fy数据类型应为整型或浮点型"
            },
            "cx":{
                "type": (float, int),
                "error_str": "cx数据类型应为整型或浮点型"
            },
            "cy":{
                "type": (float, int),
                "error_str": "cy数据类型应为整型或浮点型"
            },
            "k1":{
                "type": (float, int),
                "error_str": "k1数据类型应为整型或浮点型"
            },
            "k2":{
                "type": (float, int),
                "error_str": "k2数据类型应为整型或浮点型"
            },
            "k3":{
                "type": (float, int),
                "error_str": "k3数据类型应为整型或浮点型"
            },
            "p1":{
                "type": (float, int),
                "error_str": "p1数据类型应为整型或浮点型"
            },
            "p2":{
                "type": (float, int),
                "error_str": "p2数据类型应为整型或浮点型"
            },
            "extrinsic":{
                "type": "4*4 list float or int",
                "error_str": "extrinsic数据类型应为4*4的浮点型或整型的列表"
            }
        }
    },
    "fisheye":{
        "optional":{
            "fov":{
                "type": (float, int),
                "error_str": "fov数据类型应为整型或浮点型"
            },
            "camera_euler_z":{
                "type": (float, int),
                "error_str": "camera_euler_z数据类型应为整型或浮点型"
            }
        },
        "necessary":{
            "fx":{
                "type": (float, int),
                "error_str": "fx数据类型应为整型或浮点型"
            },
            "fy":{
                "type": (float, int),
                "error_str": "fy数据类型应为整型或浮点型"
            },
            "cx":{
                "type": (float, int),
                "error_str": "cx数据类型应为整型或浮点型"
            },
            "cy":{
                "type": (float, int),
                "error_str": "cy数据类型应为整型或浮点型"
            },
            "k1":{
                "type": (float, int),
                "error_str": "k1数据类型应为整型或浮点型"
            },
            "k2":{
                "type": (float, int),
                "error_str": "k2数据类型应为整型或浮点型"
            },
            "k3":{
                "type": (float, int),
                "error_str": "k3数据类型应为整型或浮点型"
            },
            "k4":{
                "type": (float, int),
                "error_str": "k4数据类型应为整型或浮点型"
            },
            "extrinsic":{
                "type": "4*4 list float or int",
                "error_str": "extrinsic数据类型应为4*4的浮点型或整型的列表"
            }
        }
    },
    "omnidirectional":{
        "optional":{
            "fov":{
                "type": (float, int),
                "error_str": "fov数据类型应为整型或浮点型"
            },
            "camera_euler_z":{
                "type": (float, int),
                "error_str": "camera_euler_z数据类型应为整型或浮点型"
            }
        },
        "necessary":{
            "fx":{
                "type": (float, int),
                "error_str": "fx数据类型应为整型或浮点型"
            },
            "fy":{
                "type": (float, int),
                "error_str": "fy数据类型应为整型或浮点型"
            },
            "cx":{
                "type": (float, int),
                "error_str": "cx数据类型应为整型或浮点型"
            },
            "cy":{
                "type": (float, int),
                "error_str": "cy数据类型应为整型或浮点型"
            },
            "k1":{
                "type": (float, int),
                "error_str": "k1数据类型应为整型或浮点型"
            },
            "k2":{
                "type": (float, int),
                "error_str": "k2数据类型应为整型或浮点型"
            },
            "k3":{
                "type": (float, int),
                "error_str": "k3数据类型应为整型或浮点型"
            },
            "p1":{
                "type": (float, int),
                "error_str": "p1数据类型应为整型或浮点型"
            },
            "p2":{
                "type": (float, int),
                "error_str": "p2数据类型应为整型或浮点型"
            },
            "xi":{
                "type": (float, int),
                "error_str": "xi数据类型应为整型或浮点型"
            },
            "extrinsic":{
                "type": "4*4 list float or int",
                "error_str": "extrinsic数据类型应为4*4的浮点型或整型的列表"
            }
        }
    },
    "qingzhou":{
        "optional":{
            "fov":{
                "type": (float, int),
                "error_str": "fov数据类型应为整型或浮点型"
            },
            "camera_euler_z":{
                "type": (float, int),
                "error_str": "camera_euler_z数据类型应为整型或浮点型"
            }
        },
        "necessary":{
            "fx":{
                "type": (float, int),
                "error_str": "fx数据类型应为整型或浮点型"
            },
            "fy":{
                "type": (float, int),
                "error_str": "fy数据类型应为整型或浮点型"
            },
            "cx":{
                "type": (float, int),
                "error_str": "cx数据类型应为整型或浮点型"
            },
            "cy":{
                "type": (float, int),
                "error_str": "cy数据类型应为整型或浮点型"
            },
            "extrinsic":{
                "type": "4*4 list float or int",
                "error_str": "extrinsic数据类型应为4*4的浮点型或整型的列表"
            }
        }
    },
    "scaramuzza":{
        "optional":{
            "fov":{
                "type": (float, int),
                "error_str": "fov数据类型应为整型或浮点型"
            },
            "camera_euler_z":{
                "type": (float, int),
                "error_str": "camera_euler_z数据类型应为整型或浮点型"
            }
        },
        "necessary":{
            "affine_params":{
                "type": "",
                "error_str": "affine_params 参数检查出错"
            },
            "inv_poly_params":{
                "type": "20 位的 float list",
                "error_str": "inv_poly_params 参数检查出错"
            },
            "extrinsic":{
                "type": "4*4 list float or int",
                "error_str": "extrinsic数据类型应为4*4的浮点型或整型的列表"
            }
        }
    }
}