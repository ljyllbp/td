

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
TD_VERSION = "1.0.0"

BUCKET = "default"

PACKAGE_SPECIAL_STRING = "__TESTINPACKAGE__"

CALL_BACK_SUCCESS_COUNT = 5000

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
    }
}