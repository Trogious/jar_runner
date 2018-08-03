import boto3
from botocore.client import Config
import os


def handler(event, context):
    sns = boto3.client('sns')
    key = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']
    s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
    url = s3.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=1800)
    message = 'Jar execution result is now ready: ' + key + '.\n\nTo download, click here: ' + url + '\n\n\n'
    sns.publish(TopicArn=os.getenv('JAR_LAMBDA_NOTIFY_SNS_ARN'), Subject='JAR execution complete', Message=message)
    return key
