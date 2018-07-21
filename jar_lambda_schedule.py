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


def launch_instance():
    ec2 = boto3.client('ec2')
    AMI = 'ami-43eec3a8'
    USER_DATA = ''
    resp = ec2.run_instances(ImageId=AMI, InstanceType='t2.micro', MinCount=1, MaxCount=1, InstanceInitiatedShutdownBehavior='terminate',  # KeyName='MyEC3Key',  # NetworkInterfaces=[{'AssociatePublicIpAddress': False, 'DeviceIndex': 0}],
                             IamInstanceProfile={'Arn': 'arn:aws:iam::978925540073:instance-profile/EC2_S3_SQS_Full'}, UserData=base64.b64decode(USER_DATA).decode('utf8'))
    return resp['Instances'][0]['InstanceId']


def handler(event, context):
    resp = get_error_resp('unknown error')
    bucket = os.getenv('JAR_LAMBDA_LIST_JARS_BUCKET')
    if bucket is None:
        resp = get_error_resp('BUCKET not provided')
    else:
        queue_name = os.getenv('JAR_LAMBDA_QUEUE_NAME')
        if queue_name is None:
            resp = get_error_resp('QUEUE_NAME not provided')
        elif event is not None and 'body' in event.keys():
            try:
                body = json.loads(event['body'])
                jar_name = body['name']
                resp = get_error_resp('provided jar cannot be found')
                for key in get_s3_contents(bucket):
                    if key['Key'].endswith('.jar'):
                        if key['Key'].replace('jars/', '') == jar_name:
                            queue_resp = send_to_queue(queue_name, jar_name)
                            instance_id = 'x'  # launch_instance()
                            resp = response({'status': 'scheduled ' + queue_resp.get('MessageId') + ' ' + instance_id}, 200)
                            break
            except Exception as e:
                resp = get_error_resp(e)
        else:
            resp = get_error_resp('no or malformed jar name')
    return resp
