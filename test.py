#!/usr/local/bin/python3
import logging
import json
import boto3
import os
import zipfile
import io
import base64
from botocore.client import Config
import requests


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


# s3 = boto3.client('s3')
# r3 = boto3.resource('s3')
# try:
#     bt = b'asda'
#     print(bt.replace(b'a', b'b'))
#     for b in s3.list_buckets()['Buckets']:
#         if b['Name'].startswith('jr'):
#             b = r3.Bucket(b['Name'])
#             print(b)
# except s3.exceptions.NoSuchKey as e:
#     print('no such key')
#     print(e)
# except Exception as e:
#     print(e)

def get_instances_count(ec2, stack_name):
    count = 0
    try:
        inst = ec2.describe_instances()
        for r in inst['Reservations']:
            for i in r['Instances']:
                print(i['InstanceId'])
                if int(i['State']['Code']) != 48:
                    print(i['State'])
                    if 'Tags' in i.keys():
                        for t in i['Tags']:
                            if t['Key'] == 'Name' and t['Value'].endswith('JarExecutor-' + stack_name):
                                count += 1
    except Exception as e:
        print('Error describing instances: %s\n' % str(e))
    return count


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_session():
    access_key = os.getenv('JAR_LAMBDA_ACCESS_KEY')
    secret_key = os.getenv('JAR_LAMBDA_SECRET_KEY')
    if None in [access_key, secret_key]:
        raise Exception('KEYs not set')
    session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name='eu-central-1')
    return session


def handler(event, context):
    key = 'x'
    bucket = 'y'
    try:
        session = get_session()
        s3 = session.client('s3', config=boto3.session.Config(signature_version='s3v4'), region_name='eu-central-1')
        url = s3.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
        print(url)
        resp = requests.get(url)
        print(resp)
    except Exception as e:
        print(e)
    return key


handler(0, 0)
