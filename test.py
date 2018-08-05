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
import sys, datetime, hashlib, hmac, urllib, time


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


class CloudWatchLogger:
    def __init__(self, group_name, stream_name):
        self.logs = None
        self.stream = None
        self.sequence_token = None
        self.group_name = group_name
        self.stream_name = stream_name

    def is_enabled(self):
        if self.stream is None:
            try:
                self.logs = boto3.client('logs', aws_access_key_id='', aws_secret_access_key='')
                self.stream = self.logs.create_log_stream(logGroupName=self.group_name, logStreamName=self.stream_name)
            except Exception:
                if self.logs is not None:
                    try:
                        self.stream_name = self.stream_name + '_' + str(self.get_current_timestamp())
                        self.stream = self.logs.create_log_stream(logGroupName=self.group_name, logStreamName=self.stream_name)
                    except Exception:
                        pass
        return self.stream is not None

    def get_current_timestamp(self):
        return int(round(time.time() * 1000.0))

    def log(self, msg):
        if self.is_enabled():
            try:
                if self.sequence_token is None:
                    self.sequence_token = self.logs.put_log_events(logGroupName=self.group_name, logStreamName=self.stream_name, logEvents=[{'timestamp': self.get_current_timestamp(), 'message': msg}])['nextSequenceToken']
                else:
                    self.sequence_token = self.logs.put_log_events(logGroupName=self.group_name, logStreamName=self.stream_name, logEvents=[{'timestamp': self.get_current_timestamp(), 'message': msg}], sequenceToken=self.sequence_token)['nextSequenceToken']
            except Exception:
                pass


if len(sys.argv) > 1:
    logcw = CloudWatchLogger('testLG', 'testLS')
    for msg in sys.argv[1:]:
        print(msg)
        logcw.log(msg)
