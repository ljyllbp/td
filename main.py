from upload import *
from upload.pointcloud import *
from upload.text import *
from upload.audio import *
from upload.segment_audio import *
from upload.video import *
from upload.segment_video import *
from upload.image import *
from upload.segment_image import *
from config import *
from export import *
from utils import td_tool
import os
import sys


def get_upload_class(host, ds_id, ak):
    data_type = upload.get_data_type(host,ds_id, ak)
    if data_type == "fushion_sensor_pointcloud":
        upload_class = pointcloud_upload
    elif data_type == "text":
        upload_class = text_upload
    elif data_type == "image":
        upload_class = image_upload
    elif data_type == "segment_image":
        upload_class = segment_image_upload
    elif data_type == "audio":
        upload_class = audio_upload
    elif data_type == "segment_audio":
        upload_class = segment_audio_upload
    elif data_type == "video":
        upload_class = video_upload
    elif data_type == "segment_video":
        upload_class = segment_video_upload
    else:
        raise Exception(f"暂不支持{data_type}类型")

    return upload_class

def mk_td():
    td = td_tool.Td("Testin commandline tool")

    td.add_optional("help", little_name="h", detail=f"help for {TD_NAME}")

    command_upload = td_tool.Command("upload", "upload local files")
    
    command_upload.add_mandatory("ds_id", type=str)
    command_upload.add_mandatory("ak", type=str)
    command_upload.add_mandatory("data_root", type=str)

    command_upload.add_optional("force_compressed",little_name='f', default_value=False, detail="compress pcd file, pcd file may be modified,default false")
    command_upload.add_optional("help", little_name='h', detail=f"help for upload")
    command_upload.add_optional("host", type=str, default_value=PRODUCTION_HOST, detail=f"host of the platform, default \"{PRODUCTION_HOST}\"")
    command_upload.add_optional("retry_count", type=int, little_name='r', default_value=10, detail="download retry count, default 10")
    command_upload.add_optional("simplify_pcd", little_name='s', default_value=False, detail=" streamline pcd file, default false")
    command_upload.add_optional("thread_num", type=int, little_name='t', default_value=None, detail="thread number, default cpu count")

    td.add_command(command_upload)


    command_export = td_tool.Command("export", "export files")
    command_export.add_mandatory("task_batch_key", type=str)
    command_export.add_mandatory("ak", type=str)
    command_export.add_mandatory("out", type=str)

    command_export.add_optional("download_type", type=str, little_name='d', default_value="label", detail="download type: label, original or original_and_label, default label")
    command_export.add_optional("file_name", type=str, little_name='f', default_value=None, detail="file name, default none")
    command_export.add_optional("have_more_info", little_name='m', default_value=False, detail="get user info, default false")
    command_export.add_optional("help", little_name='h', detail=f"help for export")
    command_export.add_optional("host", type=str, default_value=PRODUCTION_HOST, detail=f"host of the platform, default \"{PRODUCTION_HOST}\"")

    command_export.add_optional("operate_work_type", type=int, default_value=None, detail="operate work type, use with operate_users, default none")
    command_export.add_optional("operate_users", type=int, default_value=None, detail="operate users, use with operate_work_type, default none")

    command_export.add_optional("package_id", type=int, little_name='p', default_value=None, detail="package id, default none")
    command_export.add_optional("retry_count", type=int, little_name='r', default_value=10, detail="download retry count, default 10")

    command_export.add_optional("seg_dir_name", type=str, default_value=None, detail="segment name, default none")

    command_export.add_optional("status", type=int, little_name='s', default_value=99, detail="status, default 99")

    command_export.add_optional("task_id", type=int, little_name='t', default_value=None, detail="task id, default none")
    command_export.add_optional("thread_num", type=int, little_name='n', default_value=None, detail="thread number, default cpu count")
    command_export.add_optional("work_type", type=int, little_name='w', default_value=1, detail="work type, default 1")


    td.add_command(command_export)
    return td

def check_upload_args(args):
    data_root = args["data_root"]
    if data_root.endswith(("\\","/")):
        raise Exception(f"{data_root} 不应以‘/’,'\\'结尾")
    if not os.path.isdir(data_root):
        raise Exception(f"{data_root} 应为数据目录")
    
    retry_count = args["retry_count"]
    if retry_count < 0 :
        args["retry_count"] = 0
    elif retry_count > MAX_RETRY_COUNT:
        args["retry_count"] = MAX_RETRY_COUNT
    
    thread_num = args["thread_num"]
    if thread_num is not None:
        if thread_num <= 0 :
            args["thread_num"] = 1
        elif thread_num > MAX_THREAD_NUM:
            args["thread_num"] = MAX_THREAD_NUM

def check_export_args(args):
    out = args["out"]
    if out.endswith(("\\","/")):
        raise Exception(f"{out} 不应以‘/’,'\\'结尾")
    if not os.path.isdir(out):
        raise Exception(f"{out} 应为目录")
    
    download_type = args["download_type"]
    if download_type not in ["label", "original", "original_and_label"]:
        raise Exception(f"download_type 的值为{download_type}, 应为 label, original, original_and_label")

    retry_count = args["retry_count"]
    if retry_count < 0 :
        args["retry_count"] = 0
    elif retry_count > MAX_RETRY_COUNT:
        args["retry_count"] = MAX_RETRY_COUNT

    status = args["status"]
    if status not in [0, 1, 2, 3, 99]:
        raise Exception(f"status 的值为{status}, 应为 0, 1, 2, 3, 99")
    
    work_type = args["work_type"]
    if work_type not in [1, 2, 3, 4]:
        raise Exception(f"status 的值为{work_type}, 应为 1, 2, 3, 4")
    
    thread_num = args["thread_num"]
    if thread_num is not None:
        if thread_num <= 0 :
            args["thread_num"] = 1
        elif thread_num > MAX_THREAD_NUM:
            args["thread_num"] = MAX_THREAD_NUM

def start():
    td = mk_td()
    td.init_args()
    args = td.get_args()
    command_name = td.command[td.command_index].name
    if command_name == "upload":
        check_upload_args(args)
        upload_class = get_upload_class(args["host"], args["ds_id"], args["ak"])
        upload_ = upload_class(args["ds_id"], args["data_root"])
        upload_.set_debug(True)
        upload_.set_retry_count(args["retry_count"])
        upload_.set_host_and_ak(args["host"], args["ak"])
        if args["thread_num"] is not None:
            upload_.set_executor(args["thread_num"])
        upload_.set_pcd_option(args["simplify_pcd"], args["force_compressed"])
        upload_.start_upload()

    elif command_name == "export":
        check_export_args(args)
        export_ = Exporter(args["out"], args["task_batch_key"], args["ak"], host=args["host"])
        if args["thread_num"] is not None:
            export_.set_executor(args["thread_num"])
        export_.set_retry_count(args["retry_count"])
        export_.set_have_more_info(args["have_more_info"])
        export_.set_download_type(args["download_type"])
        export_.set_work_type(args["work_type"])
        export_.set_status(args["status"])

        export_.set_operate_work_type(args["operate_work_type"])
        export_.set_operate_users(args["operate_users"])
        export_.set_seg_dir_name(args["seg_dir_name"])
        export_.set_package_id(args["package_id"])
        export_.set_task_id(args["task_id"])
        export_.set_file_name(args["file_name"])

        export_.get_items()
        export_.download_files(True)

if __name__ == "__main__":
    start()