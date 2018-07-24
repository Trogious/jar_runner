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


def create_user_data():
    with open('./jar_ec2_execute.py', 'r') as f:
        pass
    return ''


def get_user_data():
    return create_user_data()


def launch_instance(ami_id, instance_type, instance_profile_arn):
    ec2 = boto3.client('ec2')
    resp = ec2.run_instances(ImageId=ami_id, InstanceType=instance_type, MinCount=1, MaxCount=1, InstanceInitiatedShutdownBehavior='terminate',  # KeyName='MyEC3Key',  # NetworkInterfaces=[{'AssociatePublicIpAddress': False, 'DeviceIndex': 0}],
                             IamInstanceProfile={'Arn': instance_profile_arn}, UserData=get_user_data())
    return resp['Instances'][0]['InstanceId']


def handler(event, context):
    resp = get_error_resp('unknown error')
    bucket = os.getenv('JAR_LAMBDA_LIST_JARS_BUCKET')
    queue_name = os.getenv('JAR_LAMBDA_QUEUE_NAME')
    instance_profile_arn = os.getenv('JAR_LAMBDA_INSTANCE_PROFILE_ARN')
    ami_id = os.getenv('JAR_LAMBDA_AMI_ID')
    instance_type = os.getenv('JAR_LAMBDA_EXECUTOR_INSTANCE_TYPE')
    if bucket is None:
        resp = get_error_resp('BUCKET not provided')
    elif queue_name is None:
        resp = get_error_resp('QUEUE_NAME not provided')
    elif instance_profile_arn is None:
        resp = get_error_resp('INSTANCE_PROFILE not provided')
    elif ami_id is None:
        resp = get_error_resp('AMI_ID not provided')
    elif instance_type is None:
        resp = get_error_resp('INSTANCE_TYPE not provided')
    elif event is not None and 'body' in event.keys():
        try:
            body = json.loads(event['body'])
            jar_name = body['name']
            resp = get_error_resp('provided jar cannot be found')
            for key in get_s3_contents(bucket):
                if key['Key'].endswith('.jar'):
                    if key['Key'].replace('jars/', '') == jar_name:
                        queue_resp = send_to_queue(queue_name, jar_name)
                        instance_id = launch_instance()
                        resp = response({'status': 'scheduled ' + queue_resp.get('MessageId') + ' ' + instance_id}, 200)
                        break
        except Exception as e:
            resp = get_error_resp(e)
    else:
        resp = get_error_resp('invalid input parameters')
    return resp
