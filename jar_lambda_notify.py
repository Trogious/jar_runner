import boto3
from botocore.client import Config
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_session():
    access_key = os.getenv('JAR_LAMBDA_ACCESS_KEY')
    secret_key = os.getenv('JAR_LAMBDA_SECRET_KEY')
    region = os.getenv('JAR_LAMBDA_REGION')
    if None in [access_key, secret_key, region]:
        raise Exception('KEYs not set')
    session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
    return session


def handler(event, context):
    sns = boto3.client('sns')
    key = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']
    try:
        session = get_session()
        s3 = session.client('s3', config=Config(signature_version='s3v4'))
        url = s3.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=1800)
        message = 'Jar execution result is now ready: ' + key + '.\n\nTo download, click here: ' + url + '\n\n\n'
        sns.publish(TopicArn=os.getenv('JAR_LAMBDA_NOTIFY_SNS_ARN'), Subject='JAR execution complete', Message=message)
    except Exception as e:
        logger.exception(e)
    return key
