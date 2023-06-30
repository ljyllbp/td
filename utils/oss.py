from oss2 import Auth, Bucket, StsAuth
import oss2
import boto3
from botocore.client import Config
from config import *


class AliyunClass(object):
    '''阿里云OSS'''

    @staticmethod
    def upload(oss_file_path, local_file_path, oss_config):
        '''上传文件'''

        auth = StsAuth(oss_config["access_key"], oss_config["secret_key"], oss_config["token"])
        bucket = Bucket(auth, oss_config["endpoint"], oss_config["bucket"], is_cname=True)
        oss_file_path = oss_file_path.lstrip('/')

        result = oss2.resumable_upload(bucket, oss_file_path, local_file_path, multipart_threshold=ALI_OSS_MULTIPART_THRESHOLD, part_size=ALI_OSS_PART_SIZE, num_threads=ALI_OSS_NUM_THREADS)
        # result = bucket.put_object_from_file(oss_file_path, local_file_path)
        assert result.status == 200
        
    @staticmethod
    def download(oss_file_path, local_file_path, oss_config):
        '''下载文件'''        
        auth = StsAuth(oss_config["access_key"], oss_config["secret_key"], oss_config["token"])
        bucket = Bucket(auth, oss_config["endpoint"], oss_config["bucket"], is_cname=True)
        oss_file_path = oss_file_path.lstrip('/')

        oss2.resumable_download(bucket, oss_file_path, local_file_path, multiget_threshold=ALI_OSS_MULTIPART_THRESHOLD, part_size=ALI_OSS_PART_SIZE, num_threads=ALI_OSS_NUM_THREADS)

        # result = bucket.get_object_to_file(oss_file_path, local_file_path)
        # assert result.status == 200

class MinioClass(object):
    '''Minio'''

    @staticmethod
    def upload(oss_file_path, local_file_path, oss_config):
        '''上传文件'''
        
        oss_file_path = "/".join(oss_file_path.split("/")[2:])

        s3_client = boto3.client(
            's3',
            endpoint_url = oss_config["endpoint"],
            aws_access_key_id = oss_config["access_key"],
            aws_secret_access_key = oss_config["secret_key"],
            aws_session_token = oss_config["token"],
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        with open(local_file_path, "rb") as fp:
            s3_client.upload_fileobj(fp, oss_config["bucket"], oss_file_path)

    @staticmethod
    def download(oss_file_path, local_file_path, oss_config):
        '''下载文件'''
        oss_file_path = "/".join(oss_file_path.split("/")[2:])

        s3_client = boto3.client(
            's3',
            endpoint_url = oss_config["endpoint"],
            aws_access_key_id = oss_config["access_key"],
            aws_secret_access_key = oss_config["secret_key"],
            aws_session_token = oss_config["token"],
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        with open(local_file_path, "rb") as fp:
            s3_client.download_fileobj(oss_config["bucket"], oss_file_path, fp)