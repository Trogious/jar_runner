#!/usr/local/bin/python3
import logging
import json
import boto3
import os
import zipfile
import io
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def zip_website(path):
    zipped_buf = io.BytesIO()
    with zipfile.ZipFile(zipped_buf, 'w') as zip_file:
        for root, dirs, files in os.walk(path):
            for file in files:
                slash = '' if path.endswith('/') else '/'
                path_to_write = os.path.join(root, file)
                in_arch_name = path_to_write.replace(path + slash, '')
                zip_file.write(path_to_write, in_arch_name)
    return base64.b64encode(zipped_buf.getvalue())


s3 = boto3.client('s3')
r3 = boto3.resource('s3')
try:
    bt = b'asda'
    print(bt.replace(b'a', b'b'))
    for b in s3.list_buckets()['Buckets']:
        if b['Name'].startswith('jr'):
            b = r3.Bucket(b['Name'])
            print(b)
except s3.exceptions.NoSuchKey as e:
    print('no such key')
    print(e)
except Exception as e:
    print(e)
