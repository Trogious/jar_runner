import boto3
from botocore.client import Config


def handler(event, context):
    sns = boto3.client('sns')
    key = event['Records'][0]['s3']['object']['key']
    s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
    url = s3.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': 'rtp-output-results', 'Key': key})
    message = 'RTP test result is now ready: ' + key + '.\n\nTo download, click here: ' + url + '\n\n\n'
    sns.publish(TopicArn='arn:aws:sns:eu-central-1:978925540073:rtp_lambda_notifications', Subject='RTP test complete', Message=message)
    return key
