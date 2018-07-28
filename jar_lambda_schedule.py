import boto3
import json
import os
import base64


def response(body, status):
    resp = {"isBase64Encoded": False, "statusCode": status, "body": json.dumps(body), 'headers': {'Access-Control-Allow-Origin': '*'}}
    return resp


def get_error_resp(error):
    return response({'message': str(error)}, 500)


def get_unauthorized_resp(error):
    return response({'message': str(error)}, 401)


def get_s3_contents(bucket):
    s3 = boto3.client('s3')
    return s3.list_objects(Bucket=bucket, Prefix='jars/')['Contents']


def send_to_queue(queue_name, jar_name):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return queue.send_message(MessageBody='{"name":"' + jar_name + '"}')


def get_user_data(bucket_in, bucket_out, queue_name, region):
    ENCODING = 'utf8'
    user_data = '#!/bin/sh -\n'
    with open('./jar_ec2_execute.py', 'rb') as f:
        executor = f.read()
        executor = executor.replace(b'BUCKET_NAME_IN', bucket_in.encode(ENCODING))
        executor = executor.replace(b'BUCKET_NAME_OUT', bucket_out.encode(ENCODING))
        executor = executor.replace(b'QUEUE_NAME', queue_name.encode(ENCODING))
        executor = executor.replace(b'REGION', region.encode(ENCODING))
        executor = base64.b64encode(executor).decode(ENCODING)
        user_data += "echo '" + executor + "' | base64 -d - > /home/ec2-user/jar_ec2_execute.py\n"
    user_data += 'chmod 700 /home/ec2-user/jar_ec2_execute.py\n'
    user_data += 'chown ec2-user:ec2-user /home/ec2-user/jar_ec2_execute.py\n'
    user_data += 'su - ec2-user -c /home/ec2-user/jar_ec2_execute.py\n'
    user_data += '/usr/sbin/poweroff\n'
    return user_data


def get_instances_count(ec2, stack_name):
    count = 0
    try:
        inst = ec2.describe_instances()
        for r in inst['Reservations']:
            if 'Instances' in r.keys():
                for i in r['Instances']:
                    if int(i['State']['Code']) < 49:
                        if 'Tags' in i.keys():
                            for t in i['Tags']:
                                if t['Key'] == 'Name' and t['Value'].endswith('JarExecutor-' + stack_name):
                                    count += 1
    except Exception:
        count = 9999
    return count


def launch_instance(ami_id, instance_type, instance_profile_arn, stack_name, bucket_in, bucket_out, queue_name, region, instance_limit):
    ec2 = boto3.client('ec2')
    if get_instances_count(ec2, stack_name) < instance_limit:
        resp = ec2.run_instances(ImageId=ami_id, InstanceType=instance_type, MinCount=1, MaxCount=1, InstanceInitiatedShutdownBehavior='terminate',  # KeyName='MyEC3Key',  # NetworkInterfaces=[{'AssociatePublicIpAddress': False, 'DeviceIndex': 0}],
                                 IamInstanceProfile={'Arn': instance_profile_arn}, UserData=get_user_data(bucket_in, bucket_out, queue_name, region),
                                 TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'JarExecutor-' + stack_name}]}])
        return resp['Instances'][0]['InstanceId']
    else:
        return None


def handler(event, context):
    resp = get_error_resp('unknown error')
    bucket_in = os.getenv('JAR_LAMBDA_BUCKET_IN')
    queue_name = os.getenv('JAR_LAMBDA_QUEUE_NAME')
    instance_profile_arn = os.getenv('JAR_LAMBDA_INSTANCE_PROFILE_ARN')
    ami_id = os.getenv('JAR_LAMBDA_AMI_ID')
    instance_type = os.getenv('JAR_LAMBDA_EXECUTOR_INSTANCE_TYPE')
    stack_name = os.getenv('JAR_LAMBDA_STACK_NAME')
    bucket_out = os.getenv('JAR_LAMBDA_BUCKET_OUT')
    region = os.getenv('JAR_LAMBDA_REGION')
    instance_limit = int(os.getenv('JAR_LAMBDA_INSTANCE_LIMIT', 5))
    if bucket_in is None:
        resp = get_error_resp('BUCKET not provided')
    elif queue_name is None:
        resp = get_error_resp('QUEUE_NAME not provided')
    elif instance_profile_arn is None:
        resp = get_error_resp('INSTANCE_PROFILE not provided')
    elif ami_id is None:
        resp = get_error_resp('AMI_ID not provided')
    elif instance_type is None:
        resp = get_error_resp('INSTANCE_TYPE not provided')
    elif stack_name is None:
        resp = get_error_resp('STACK not provided')
    elif bucket_out is None:
        resp = get_error_resp('BUCKET_OUT not provided')
    elif region is None:
        resp = get_error_resp('REGION not provided')
    elif instance_limit is None:
        resp = get_error_resp('LIMIT not provided')
    elif event is not None and 'body' in event.keys():
        try:
            body = json.loads(event['body'])
            jar_name = body['name']
            resp = get_error_resp('provided jar cannot be found')
            for key in get_s3_contents(bucket_in):
                if key['Key'].endswith('.jar'):
                    if key['Key'].replace('jars/', '') == jar_name:
                        queue_resp = send_to_queue(queue_name, jar_name)
                        instance_id = launch_instance(ami_id, instance_type, instance_profile_arn, stack_name, bucket_in, bucket_out, queue_name, region, instance_limit)
                        if instance_id is None:
                            resp = response({'status': 'scheduled ' + queue_resp.get('MessageId') + ' ' + instance_id}, 200)
                        else:
                            resp = response({'status': 'cannot launch instance for ' + queue_resp.get('MessageId')}, 200)
                        break
        except Exception as e:
            resp = get_error_resp(e)
    else:
        resp = get_error_resp('invalid input parameters')
    return resp
