import logging
import os
import boto3
from botocore.client import Config

import os
import mimetypes

# from examples.progress import Progress
from minio import Minio
from minio.error import InvalidResponseError

# these are local dev credentials not an issue being exposed
access_key = "BPtnRYnuDVHVLg7j"
secret_key = "UzbTKQaofqzZT391e26hWO9Rljt0AuFR"


class S3Connector:
    def __init__(
        self,
        bucket_name,
        endpoint="localhost:9000",
        access_key=access_key,
        secret_key=secret_key,
    ):
        self.client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=False
        )
        self.bucket_name = bucket_name

    def put_file(self, file_path, object_name, bucket_name=None, content_type=None):
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            with open(file_path, "rb") as file_data:
                file_stat = os.stat(file_path)
                file_type = (
                    content_type
                    or mimetypes.guess_type(file_path)[0]
                    or "application/octet-stream"
                )
                logging.info(
                    f"Uploading file '{file_path}' to bucket '{bucket_name}' as '{object_name}' filetype={file_type}."
                )
                self.client.put_object(
                    bucket_name,
                    object_name,
                    file_data,
                    file_stat.st_size,
                    content_type=content_type,  # type: ignore
                )
        except InvalidResponseError as err:
            logging.error(err)


# Put a file with progress.
# progress = Progress()
# try:
#     with open('my-testfile', 'rb') as file_data:
#         file_stat = os.stat('my-testfile')
#         client.put_object('my-bucketname', 'my-objectname',
#                           file_data, file_stat.st_size, progress=progress)
# except ResponseError as err:
#     print(err)


# class S3Connector:
#     def __init__(
#         self,
#         bucket_name,
#         create_bucket=False,
#         endpoint_url="http://0.0.0.0:9000",
#         access_key="BPtnRYnuDVHVLg7j",
#         secret_key="UzbTKQaofqzZT391e26hWO9Rljt0AuFR",
#     ):
#         self.bucket_name = bucket_name

#         self.s3 = boto3.resource(
#             "s3",
#             endpoint_url=endpoint_url,
#             aws_access_key_id=access_key,
#             aws_secret_access_key=secret_key,
#             # config=Config(signature_version="s3v4"),
#             # region_name="us-east-1",
#         )

#     def file_upload(self, file_path, file_key, **kwargs):
#         self.s3.Bucket(self.bucket_name).upload_file(file_path, file_key, **kwargs)

# def create_bucket(self):
#     try:
#         if not self.client.bucket_exists(self.bucket_name):
#             self.client.make_bucket(self.bucket_name)
#             logging.info(f"Bucket '{self.bucket_name}' created successfully.")
#     except S3Error as e:
#         logging.error(f"Error creating bucket: {e}")

# def get_object(self, key):
#     try:
#         response = self.client.get_object(self.bucket_name, key)
#         return response.read()
#     except S3Error as e:
#         logging.error(f"Error getting object: {e}")
#         return None

# def put_object(self, key, data, **kwargs):
#     try:
#         self.client.put_object(
#             self.bucket_name,
#             key,
#             data,
#             length=-1,
#             **kwargs
#             # content_type="application/octet-stream",
#         )
#         logging.info(f"Object '{key}' uploaded successfully.")
#     except S3Error as e:
#         logging.error(f"Error uploading object: {e}")

# def upload_file(self, file_path, key):
#     try:
#         self.client.fput_object(self.bucket_name, key, file_path)
#         logging.info(
#             f"File '{file_path}' uploaded to bucket '{self.bucket_name}' as '{key}'."
#         )
#     except S3Error as e:
#         logging.error(f"Error uploading file: {e}")
