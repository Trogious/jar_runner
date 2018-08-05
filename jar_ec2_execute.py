#!/usr/bin/env python3
import boto3
import subprocess
import json
import datetime
import os
import tarfile
import time

PREFIX_DIR = './results_'
RESULTS_OUT = 'results_out.txt'
RESULTS_ERR = 'results_diag.txt'


def get_current_timestamp(self):
    return int(round(time.time() * 1000.0))


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
                self.logs = boto3.client('logs')
                self.stream = self.logs.create_log_stream(logGroupName=self.group_name, logStreamName=self.stream_name)
            except Exception:
                if self.logs is not None:
                    try:
                        self.stream_name = self.stream_name + '_' + str(get_current_timestamp())
                        self.stream = self.logs.create_log_stream(logGroupName=self.group_name, logStreamName=self.stream_name)
                    except Exception:
                        pass
        return self.stream is not None

    def log(self, msg):
        if self.is_enabled():
            try:
                if self.sequence_token is None:
                    self.sequence_token = self.logs.put_log_events(logGroupName=self.group_name, logStreamName=self.stream_name, logEvents=[{'timestamp': get_current_timestamp(), 'message': msg}])['nextSequenceToken']
                else:
                    self.sequence_token = self.logs.put_log_events(logGroupName=self.group_name, logStreamName=self.stream_name, logEvents=[{'timestamp': get_current_timestamp(), 'message': msg}], sequenceToken=self.sequence_token)['nextSequenceToken']
            except Exception:
                pass


def extract_jar_name(body):
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
    time_start = datetime.datetime.now()
    date_stamp = time_start.isoformat(sep='_')[:19].replace(':', '-')
    jar_stamped = jar.replace('.jar', '') + '_' + date_stamp
    prefix_dir = PREFIX_DIR + jar_stamped + '/'
    os.mkdir(prefix_dir, 0o700)
    s3 = boto3.resource('s3')
    logger = CloudWatchLogger('LOG_GROUP', jar_stamped)
    with open(prefix_dir + RESULTS_OUT, 'wb') as fo:
        with open(prefix_dir + RESULTS_ERR, 'wb') as fe:
            logger.log('downloading')
            s3.meta.client.download_file('BUCKET_NAME_IN', 'jars/' + jar, './' + jar)
            logger.log('executing')
            args = ['java', '-jar', './' + jar]
            try:
                params_str = get_params_str()
                if params_str is not None:
                    args.append(params_str)
                    logger.log('parameters: ' + params_str)
            except Exception as e:
                logger.log(str(e))
            with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
                out, err = p.communicate()
                if out is None:
                    logger.log('no standard output')
                else:
                    fo.write(out)
                if err is None:
                    logger.log('no diagnostic output')
                else:
                    fe.write(err)
    logger.log('compressing')
    results_archive = compress_results(prefix_dir)
    logger.log('uploading: ' + results_archive)
    s3.meta.client.upload_file(results_archive, 'BUCKET_NAME_OUT', os.path.basename(results_archive), ExtraArgs={'ContentType': 'application/gzip'})
    logger.log('uploaded, execution completed in %d seconds' % (datetime.datetime.now()-time_start).total_seconds())


def main():
    logger = CloudWatchLogger('LOG_GROUP', 'jar_ec2_execute_' + str(get_current_timestamp()))
    sqs = boto3.resource('sqs', region_name='REGION')
    try:
        queue = sqs.get_queue_by_name(QueueName='QUEUE_NAME')
        for message in queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=10):
            body = message.body
            message.delete()
            execute_jar(extract_jar_name(body))
            break
    except Exception as e:
        logger.log(str(e))


if __name__ == '__main__':
    main()
