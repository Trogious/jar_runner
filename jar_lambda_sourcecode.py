import boto3
import cfnresponse
import io
import json
import logging
import os
import zipfile

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    def success(data={}):
        cfnresponse.send(event, context, cfnresponse.SUCCESS, data, physicalId)

    def failed(e):
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Data': str(e)}, physicalId)

    physicalId = event['PhysicalResourceId'] if 'PhysicalResourceId' in event else None
    logger.info('Uploaded: %s\n' % json.dumps(event['ResourceProperties']['Functions']))
    try:
        src_bucket_name = os.getenv('JAR_LAMBDA_SOURCECODE_BUCKET')
        website_bucket_name = os.getenv('JAR_LAMBDA_WEBSITE_BUCKET')
        if 'RequestType' not in event:
            success({'Data': 'No RequestType in event'})
        elif event['RequestType'] in ['Create', 'Update']:
            s3 = boto3.client('s3')
            for func in event['ResourceProperties']['Functions']:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, 'w') as zip_file:
                    zip_file.writestr('index.py', func['Code'])
                s3.put_object(Bucket=src_bucket_name, Key=func['Name'].replace('.py', '.zip'), Body=zip_buf.getvalue())
                logger.info('Uploaded: %s\n' % func['Name'])
            website_in_bucket = event['ResourceProperties']['WebsiteBucket']
            website_in_key = event['ResourceProperties']['WebsiteKey']
            website = s3.get_object(Bucket=website_in_bucket, Key=website_in_key)
            zip_buf = io.BytesIO(website['Body'].read())
            with zipfile.ZipFile(zip_buf, 'r') as zip_file:
                for f_name in zip_file.namelist():
                    s3.put_object(Bucket=website_bucket_name, Key=f_name, Body=zip_file.read(f_name))
            logger.info('Uploaded website from: %s/%s\n' % (website_in_bucket, website_in_key))
            success({'Data': 'Source code uploaded to: %s' % src_bucket_name})
        elif event['RequestType'] == 'Delete':
            s3 = boto3.resource('s3')
            for b in [src_bucket_name, website_bucket_name]:
                bucket = s3.Bucket(b)
                bucket.objects.all().delete()
                logger.info('Bucket: %s emptied\n' % b)
            success({'Data': 'Bucketes emptied'})
        else:
            success({'Data': 'Unknown RequestType'})
    except Exception as e:
        failed(e)
