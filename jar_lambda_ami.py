import logging
import cfnresponse
import json
import boto3
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
            ami_name = 'JarRunnerAMI-${AWS::StackName}'
            if not physicalId:  # AMI creation has not been requested yet
                logger.info('Waiting for EC2 to stop: %s\n' % instanceId)
                instance = ec2.Instance(instanceId)
                instance.wait_until_stopped()  # TODO: fix to work properly on this lambda re-runs after timeout
                logger.info('CreatingImage: %s\n' % ami_name)
                image = instance.create_image(Name=ami_name)
                physicalId = image.image_id
            else:
                logger.info('Continuing in awaiting image available: %s\n' % physicalId)
            waiter = ec2client.get_waiter('image_available')
            try:
                waiter.wait(ImageIds=[physicalId], WaiterConfig={'Delay': 30, 'MaxAttempts': 9})
            except WaiterError as e:
                # Request the same event but set PhysicalResourceId so that the AMI is not created again
                event['PhysicalResourceId'] = physicalId
                logger.info('Timeout reached, continuing function: %s\n' % json.dumps(event))
                lambda_client = boto3.client('lambda')
                lambda_client.invoke(FunctionName=context.invoked_function_arn, InvocationType='Event', Payload=json.dumps(event))
                return
            images = ec2client.describe_images(ImageIds=[physicalId])
            for image in images['Images']:
                snapshots = ([bdm['Ebs']['SnapshotId'] for bdm in image['BlockDeviceMappings'] if 'Ebs' in bdm and 'SnapshotId' in bdm['Ebs']])
                for snapshot in snapshots:
                    ec2.Snapshot(snapshot).create_tags(Tags=[{'Key': 'Name', 'Value': 'JarRunnerSnapshot-${AWS::StackName}'}])
            ec2client.terminate_instances(InstanceIds=[instanceId])
            success({'Data': 'AMI created: %s' % ami_name})
        else:
            success({'Data': 'Unknown RequestType'})
    except Exception as e:
        failed(e)
