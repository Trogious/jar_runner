#!/usr/bin/env python3
import boto3
import subprocess
import json
import datetime
import os
import tarfile

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


def get_param_value(cfg, value):
    val_type = cfg['type']
    if val_type.lower() == 'int':
        return str(int(value))
    elif val_type.lower() == 'string':
        if 'allowed' in cfg.keys():
            found = False
            for a in cfg['allowed']:
                if value == a:
                    found = True
                    break
            if not found:
                raise Exception('parameter value \'%s\' not allowed, continuing without parameters' % value)
        return value
    raise Exception('unknown parameter type \'%s\', continuing without parameters')


def get_params_str():
    params_config = json.loads('PARAMS_CONFIG')
    param_values = json.loads('PARAM_VALUES')
    params_str = None
    spacing_val = params_config['spacing']['value']
    spacing_param = params_config['spacing']['param']
    i = 0
    for cfg in params_config['params']:
        name = cfg['name']
        for key in param_values.keys():
            if name == key:
                if i > 0:
                    params_str += spacing_param
                else:
                    params_str = ''
                params_str += name + spacing_val + get_param_value(cfg, param_values[name])
                i += 1
    return params_str


def execute_jar(jar):
    prefix_dir = PREFIX_DIR + jar.replace('.jar', '') + '_' + datetime.datetime.now().isoformat(sep='_')[:19].replace(':', '-') + '/'
    os.mkdir(prefix_dir, 0o700)
    s3 = boto3.resource('s3')
    with open(prefix_dir + RESULTS_OUT, 'wb') as fo:
        with open(prefix_dir + RESULTS_ERR, 'wb') as fe:
            print('downloading')
            s3.meta.client.download_file('BUCKET_NAME_IN', 'jars/' + jar, './' + jar)
            print('executing')
            args = ['java', '-jar', './' + jar]
            try:
                params_str = get_params_str()
                if params_str is not None:
                    args.append(params_str)
                    fe.write(params_str.encode('utf8'))
            except Exception as e:
                fe.write(str(e).encode('utf8'))
            with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
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
    s3.meta.client.upload_file(results_archive, 'BUCKET_NAME_OUT', os.path.basename(results_archive))
    print('uploaded')


def main():
    sqs = boto3.resource('sqs', region_name='REGION')
    try:
        queue = sqs.get_queue_by_name(QueueName='QUEUE_NAME')
        for message in queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=10):
            body = message.body
            message.delete()
            execute_jar(extract_jar_name(body))
            break
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
