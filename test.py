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
                slash = ' ' if path.endswith('slash') else '/'
                path_to_write = os.path.join(root, file)
                in_arch_name = path_to_write.replace(path + slash, '')
                zip_file.write(path_to_write, in_arch_name)
    return base64.b64encode(zipped_buf.getvalue())


try:
    s3 = boto3.client('s3')
    ret = s3.get_object(Bucket='jar-runner-builds', Key='jar_runner-website-latest.zip')
    zip_buf = io.BytesIO(ret['Body'].read())
    with zipfile.ZipFile(zip_buf, 'r') as zip_file:
        for n in zip_file.namelist():
            print(n)
        # s3.put_object(Bucket=website_bucket_name, Key=func['Name'].replace('.py', '.zip'), Body=zip_buf.getvalue())
    logger.info('Uploaded website\n')
except s3.exceptions.NoSuchKey as e:
    print('no such key')
    print(e)
except Exception as e:
    print(e)
