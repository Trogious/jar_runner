#!/usr/bin/env python3
import boto3
import subprocess
import json
import datetime
import os
import tarfile

BUCKET_NAME_IN = 'rtp-input-jars'
BUCKET_NAME_OUT = 'rtp-output-results'
PREFIX_DIR = './results_'
RESULTS_OUT = 'results_out.txt'
RESULTS_ERR = 'results_diag.txt'


def extract_jar_name(body):
    print(body)
    parsed = json.loads(body)
    return parsed['name']


def compress_results(dir_path):
    archive = dir_path[:-1] + '.tgz'
    with tarfile.open(archive, 'w:gz') as tar:
        for root, dirs, files in os.walk(dir_path):
            for file_name in files:
                tar.add(root + file_name)
    return archive


def execute_jar(jar):
    prefix_dir = PREFIX_DIR + jar.replace('.jar', '') + '_' + datetime.datetime.now().isoformat(sep='_')[:19].replace(':', '-') + '/'
    os.mkdir(prefix_dir, 0o700)
    with open(prefix_dir + RESULTS_OUT, 'wb') as fo:
        with open(prefix_dir + RESULTS_ERR, 'wb') as fe:
            s3 = boto3.resource('s3')
            print('downloading')
            s3.meta.client.download_file(BUCKET_NAME_IN, 'jars/' + jar, './' + jar)
            print('executing')
            with subprocess.Popen(['java', '-jar', './' + jar], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
                out, err = p.communicate()
                if out is None:
                    print('no output')
                else:
                    fo.write(out)
                if err is None:
                    print('no diagnostic')
                else:
                    fe.write(err)
    print('compressing')
    results_archive = compress_results(prefix_dir)
    print(results_archive)
    print('uploading')
    s3.meta.client.upload_file(results_archive, BUCKET_NAME_OUT, os.path.basename(results_archive))
    print('uploaded')


def main():
    sqs = boto3.resource('sqs', region_name='eu-central-1')
    try:
        queue = sqs.get_queue_by_name(QueueName='rtp_queue_schedule')
        for message in queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=10):
            body = message.body
            message.delete()
            execute_jar(extract_jar_name(body))
            break
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
