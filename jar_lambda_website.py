import boto3
import cfnresponse
import io
import json
import logging
import zipfile

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    def success(data={}):
        cfnresponse.send(event, context, cfnresponse.SUCCESS, data, physicalId)

    def failed(e):
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Msg': str(e)}, physicalId)

    physicalId = event['PhysicalResourceId'] if 'PhysicalResourceId' in event else None
    logger.info('Request received: %s\n' % json.dumps(event))
    try:
        instanceId = event['ResourceProperties']['InstanceId']
        if not instanceId:
            raise Exception('InstanceID required')
        s3 = boto3.client('s3')
        website_bucket_name = event['ResourceProperties']['WebsiteBucket']
        if 'RequestType' not in event:
            success({'Msg': 'No RequestType in event'})
        elif event['RequestType'] == 'Delete':
            r3 = boto3.resource('s3')
            bucket = r3.Bucket(website_bucket_name)
            bucket.objects.all().delete()
            logger.info('WebsiteBucket emptied')
            success({'Msg': 'WebsiteBucket emptied'})
        elif event['RequestType'] in ['Create', 'Update']:
            param_config = event['ResourceProperties']['ExecParamConfig']['Value']
            logger.info(param_config)
            json.loads(param_config)  # verifies config json format validity
            iam = boto3.client('iam')
            access_keys = iam.create_access_key(UserName=event['ResourceProperties']['OutputPreSigner'])['AccessKey']
            lamb = boto3.client('lambda')
            current_config = lamb.get_function_configuration(FunctionName=event['ResourceProperties']['LambdaNotifyArn'])['Environment']
            env_vars = {'JAR_LAMBDA_ACCESS_KEY': access_keys['AccessKeyId'], 'JAR_LAMBDA_SECRET_KEY': access_keys['SecretAccessKey'],
                        'JAR_LAMBDA_REGION': event['ResourceProperties']['RegionName']}
            if 'Variables' in current_config.keys():
                for env_name in current_config['Variables'].keys():
                    env_vars[env_name] = current_config['Variables'][env_name]
            lamb.update_function_configuration(FunctionName=event['ResourceProperties']['LambdaNotifyArn'], Environment={'Variables': env_vars})
            website_in_bucket = event['ResourceProperties']['WebsiteSourceBucket']
            website_in_key = event['ResourceProperties']['WebsiteSourceKey']
            website = s3.get_object(Bucket=website_in_bucket, Key=website_in_key)
            zip_buf = io.BytesIO(website['Body'].read())
            with zipfile.ZipFile(zip_buf, 'r') as zip_file:
                for f_name in zip_file.namelist():
                    body = zip_file.read(f_name)
                    if f_name.endswith('.html'):
                        s3.put_object(Bucket=website_bucket_name, Key=f_name, Body=body, ContentType='text/html')
                    else:
                        if f_name.startswith('static/js/main') and f_name.endswith('.js'):
                            for ep in event['ResourceProperties']['ApiEndpoints']:
                                body = body.replace(ep['Name'].encode('ascii'), ep['URL'].encode('ascii'))
                            body = body.replace(event['ResourceProperties']['ExecParamConfig']['Name'].encode('ascii'), param_config.replace('"', '\\"').encode('ascii'))
                        s3.put_object(Bucket=website_bucket_name, Key=f_name, Body=body)
            logger.info('Uploaded website from: %s/%s\n' % (website_in_bucket, website_in_key))
            success({'Msg': 'Uploaded website from: %s/%s' % (website_in_bucket, website_in_key)})
        else:
            success({'Msg': 'Unknown RequestType'})
    except Exception as e:
        failed(e)
