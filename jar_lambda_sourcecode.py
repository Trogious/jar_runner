import boto3
import cfnresponse
import io
import json
import logging
import os
import zipfile

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def write_to_zip(zip_file, name, content):
    zip_info = zipfile.ZipInfo(name)
    zip_info.compress_type = zipfile.ZIP_DEFLATED
    zip_info.create_system = 3  # Specifies Unix
    zip_info.external_attr = 0o777 << 16  # Sets chmod 777 on the file
    zip_file.writestr(zip_info, content)


def handler(event, context):
    def success(data={}):
        cfnresponse.send(event, context, cfnresponse.SUCCESS, data, physicalId)

    def failed(e):
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Msg': str(e)}, physicalId)


    physicalId = event['PhysicalResourceId'] if 'PhysicalResourceId' in event else None
    try:
        src_bucket_name = os.getenv('JAR_LAMBDA_SOURCECODE_BUCKET')
        website_bucket_name = os.getenv('JAR_LAMBDA_WEBSITE_BUCKET')
        if 'RequestType' not in event:
            success({'Msg': 'No RequestType in event'})
        elif event['RequestType'] in ['Create', 'Update']:
            s3 = boto3.client('s3')
            website_in_bucket = event['ResourceProperties']['WebsiteSourceBucket']
            cfn_module = s3.get_object(Bucket=website_in_bucket, Key='cfnresponse.py')
            for func in event['ResourceProperties']['Functions']:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, 'w') as zip_file:
                    write_to_zip(zip_file, 'index.py', func['Code'])
                    if 'cfnresponse' in func['Code']:
                        write_to_zip(zip_file, 'cfnresponse.py', cfn_module['Body'].read())
                s3.put_object(Bucket=src_bucket_name, Key=func['Name'].replace('.py', '.zip'), Body=zip_buf.getvalue())
                logger.info('Uploaded: %s\n' % func['Name'])
            success({'Msg': 'Source code uploaded to: %s' % src_bucket_name})
        elif event['RequestType'] == 'Delete':
            s3 = boto3.resource('s3')
            for b in [src_bucket_name, website_bucket_name]:
                bucket = s3.Bucket(b)
                bucket.objects.all().delete()
                logger.info('Bucket: %s emptied\n' % b)
            success({'Msg': 'Bucketes emptied'})
        else:
            success({'Msg': 'Unknown RequestType'})
    except Exception as e:
        failed(e)
