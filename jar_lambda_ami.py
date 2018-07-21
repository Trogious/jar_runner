import boto3
import cfnresponse
import json
import logging
import os
from botocore.exceptions import WaiterError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    ec2 = boto3.resource('ec2')
    ec2client = boto3.client('ec2')

    def success(data={}):
        cfnresponse.send(event, context, cfnresponse.SUCCESS, data, physicalId)

    def failed(e):
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Data': str(e)}, physicalId)

    physicalId = event['PhysicalResourceId'] if 'PhysicalResourceId' in event else None
    logger.info('Request received: %s\n' % json.dumps(event))
    try:
        instanceId = event['ResourceProperties']['InstanceId']
        if not instanceId:
            raise Exception('InstanceID required')
        if 'RequestType' not in event:
            success({'Data': 'No RequestType in event'})
        elif event['RequestType'] == 'Delete':
            if not physicalId.startswith('ami-'):
                raise Exception('Unknown PhysicalId: %s' % physicalId)
            images = ec2client.describe_images(ImageIds=[physicalId])
            for image in images['Images']:
                ec2.Image(image['ImageId']).deregister()
                snapshots = ([bdm['Ebs']['SnapshotId'] for bdm in image['BlockDeviceMappings'] if 'Ebs' in bdm and 'SnapshotId' in bdm['Ebs']])
                for snapshot in snapshots:
                    ec2.Snapshot(snapshot).delete()
            success({'Data': 'AMIs and snapshots Deleted'})
        elif event['RequestType'] in ['Create', 'Update']:
            stack_name = os.getenv('JAR_LAMBDA_STACK_NAME', '')
            ami_name = 'JarRunnerAMI-' + stack_name
            if not physicalId:  # AMI creation has not been requested yet
                logger.info('Waiting for EC2 to stop: %s\n' % instanceId)
                instance = ec2.Instance(instanceId)
                instance.wait_until_stopped()  # TODO: fix re-runs
                logger.info('Creating image: %s\n' % ami_name)
                image = instance.create_image(Name=ami_name)
                physicalId = image.image_id
            else:
                logger.info('Continuing in awaiting image available: %s\n' % physicalId)
            waiter = ec2client.get_waiter('image_available')
            try:
                waiter.wait(ImageIds=[physicalId], WaiterConfig={'Delay': 30, 'MaxAttempts': 9})
            except WaiterError as e:
                event['PhysicalResourceId'] = physicalId
                logger.info('Timeout reached, continuing function: %s\n' % json.dumps(event))
                lambda_client = boto3.client('lambda')
                lambda_client.invoke(FunctionName=context.invoked_function_arn, InvocationType='Event', Payload=json.dumps(event))
                return
            images = ec2client.describe_images(ImageIds=[physicalId])
            for image in images['Images']:
                ec2.Image(image['ImageId']).create_tags(Tags=[{'Key': 'Name', 'Value': 'JarRunnerAMI-' + stack_name}])
                snapshots = ([bdm['Ebs']['SnapshotId'] for bdm in image['BlockDeviceMappings'] if 'Ebs' in bdm and 'SnapshotId' in bdm['Ebs']])
                for snapshot in snapshots:
                    ec2.Snapshot(snapshot).create_tags(Tags=[{'Key': 'Name', 'Value': 'JarRunnerSnapshot-' + stack_name}])
            ec2client.terminate_instances(InstanceIds=[instanceId])
            boto3.client('s3').put_bucket_notification_configuration(
                Bucket=os.getenv('JAR_LAMBDA_OUTPUT_BUCKET'),
                NotificationConfiguration={'LambdaFunctionConfigurations':
                                           [{'LambdaFunctionArn': os.getenv('JAR_LAMBDA_NOTIFY_FUNCTION_ARN'),
                                            'Events': ['s3:ObjectCreated:Post', 's3:ObjectCreated:Put']}]})
            success({'Data': 'AMI created: %s' % ami_name})
        else:
            success({'Data': 'Unknown RequestType'})
    except Exception as e:
        failed(e)