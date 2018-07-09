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
    USER_DATA = 'IyEvYmluL3NoIC0KeXVtIGluc3RhbGwgLXkgcHl0aG9uMyBqYXZhLTEuOC4wLW9wZW5qZGsueDg2XzY0CnBpcDMgaW5zdGFsbCBib3RvMwplY2hvICdJeUV2ZFhOeUwySnBiaTlsYm5ZZ2NIbDBhRzl1TXdwcGJYQnZjblFnWW05MGJ6TUthVzF3YjNKMElITjFZbkJ5YjJObGMzTUthVzF3YjNKMElHcHpiMjRLYVcxd2IzSjBJR1JoZEdWMGFXMWxDbWx0Y0c5eWRDQnZjd29LUWxWRFMwVlVYMDVCVFVWZlNVNGdQU0FuY25Sd0xXbHVjSFYwTFdwaGNuTW5Da0pWUTB0RlZGOU9RVTFGWDA5VlZDQTlJQ2R5ZEhBdGIzVjBjSFYwTFhKbGMzVnNkSE1uQ2xCU1JVWkpXRjlFU1ZJZ1BTQW5MaTl5WlhOMWJIUnpYeWNLVWtWVFZVeFVVMTlQVlZRZ1BTQW5jbVZ6ZFd4MGMxOXZkWFF1ZEhoMEp3cFNSVk5WVEZSVFgwVlNVaUE5SUNkeVpYTjFiSFJ6WDJWeWNpNTBlSFFuQ2dvS1pHVm1JR1Y0ZEhKaFkzUmZhbUZ5WDI1aGJXVW9ZbTlrZVNrNkNpQWdJQ0J3Y21sdWRDaGliMlI1S1FvZ0lDQWdjR0Z5YzJWa0lEMGdhbk52Ymk1c2IyRmtjeWhpYjJSNUtRb2dJQ0FnY21WMGRYSnVJSEJoY25ObFpGc25ibUZ0WlNkZENnb0taR1ZtSUdOdmJYQnlaWE56WDNKbGMzVnNkSE1vWkdseVgzQmhkR2dwT2dvZ0lDQWdhVzF3YjNKMElIUmhjbVpwYkdVS0lDQWdJR0Z5WTJocGRtVWdQU0JrYVhKZmNHRjBhRnM2TFRGZElDc2dKeTUwWjNvbkNpQWdJQ0IzYVhSb0lIUmhjbVpwYkdVdWIzQmxiaWhoY21Ob2FYWmxMQ0FuZHpwbmVpY3BJR0Z6SUhSaGNqb0tJQ0FnSUNBZ0lDQm1iM0lnY205dmRDd2daR2x5Y3l3Z1ptbHNaWE1nYVc0Z2IzTXVkMkZzYXloa2FYSmZjR0YwYUNrNkNpQWdJQ0FnSUNBZ0lDQWdJR1p2Y2lCbWFXeGxYMjVoYldVZ2FXNGdabWxzWlhNNkNpQWdJQ0FnSUNBZ0lDQWdJQ0FnSUNCMFlYSXVZV1JrS0hKdmIzUWdLeUJtYVd4bFgyNWhiV1VwQ2lBZ0lDQnlaWFIxY200Z1lYSmphR2wyWlFvS0NtUmxaaUJsZUdWamRYUmxYMnBoY2locVlYSXBPZ29nSUNBZ2NISmxabWw0WDJScGNpQTlJRkJTUlVaSldGOUVTVklnS3lCcVlYSXVjbVZ3YkdGalpTZ25MbXBoY2ljc0lDY25LU0FySUNkZkp5QXJJR1JoZEdWMGFXMWxMbVJoZEdWMGFXMWxMbTV2ZHlncExtbHpiMlp2Y20xaGRDaHpaWEE5SjE4bktWczZNVGxkTG5KbGNHeGhZMlVvSnpvbkxDQW5MU2NwSUNzZ0p5OG5DaUFnSUNCdmN5NXRhMlJwY2lod2NtVm1hWGhmWkdseUxDQXdiemN3TUNrS0lDQWdJSGRwZEdnZ2IzQmxiaWh3Y21WbWFYaGZaR2x5SUNzZ1VrVlRWVXhVVTE5UFZWUXNJQ2QzWWljcElHRnpJR1p2T2dvZ0lDQWdJQ0FnSUhkcGRHZ2diM0JsYmlod2NtVm1hWGhmWkdseUlDc2dVa1ZUVlV4VVUxOUZVbElzSUNkM1lpY3BJR0Z6SUdabE9nb2dJQ0FnSUNBZ0lDQWdJQ0J6TXlBOUlHSnZkRzh6TG5KbGMyOTFjbU5sS0Nkek15Y3BDaUFnSUNBZ0lDQWdJQ0FnSUhCeWFXNTBLQ2RrYjNkdWJHOWhaR2x1WnljcENpQWdJQ0FnSUNBZ0lDQWdJSE16TG0xbGRHRXVZMnhwWlc1MExtUnZkMjVzYjJGa1gyWnBiR1VvUWxWRFMwVlVYMDVCVFVWZlNVNHNJQ2RxWVhKekx5Y2dLeUJxWVhJc0lDY3VMeWNnS3lCcVlYSXBDaUFnSUNBZ0lDQWdJQ0FnSUhCeWFXNTBLQ2RsZUdWamRYUnBibWNuS1FvZ0lDQWdJQ0FnSUNBZ0lDQjNhWFJvSUhOMVluQnliMk5sYzNNdVVHOXdaVzRvV3lkcVlYWmhKeXdnSnkxcVlYSW5MQ0FuTGk4bklDc2dhbUZ5WFN3Z2MzUmtiM1YwUFhOMVluQnliMk5sYzNNdVVFbFFSU3dnYzNSa1pYSnlQWE4xWW5CeWIyTmxjM011VUVsUVJTa2dZWE1nY0RvS0lDQWdJQ0FnSUNBZ0lDQWdJQ0FnSUc5MWRDd2daWEp5SUQwZ2NDNWpiMjF0ZFc1cFkyRjBaU2dwQ2lBZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0JwWmlCdmRYUWdhWE1nVG05dVpUb0tJQ0FnSUNBZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0J3Y21sdWRDZ25ibThnYjNWMGNIVjBKeWtLSUNBZ0lDQWdJQ0FnSUNBZ0lDQWdJR1ZzYzJVNkNpQWdJQ0FnSUNBZ0lDQWdJQ0FnSUNBZ0lDQWdabTh1ZDNKcGRHVW9iM1YwS1FvZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0FnYVdZZ1pYSnlJR2x6SUU1dmJtVTZDaUFnSUNBZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0FnY0hKcGJuUW9KMjV2SUdWeWNtOXlKeWtLSUNBZ0lDQWdJQ0FnSUNBZ0lDQWdJR1ZzYzJVNkNpQWdJQ0FnSUNBZ0lDQWdJQ0FnSUNBZ0lDQWdabVV1ZDNKcGRHVW9aWEp5S1FvZ0lDQWdjSEpwYm5Rb0oyTnZiWEJ5WlhOemFXNW5KeWtLSUNBZ0lISmxjM1ZzZEhOZllYSmphR2wyWlNBOUlHTnZiWEJ5WlhOelgzSmxjM1ZzZEhNb2NISmxabWw0WDJScGNpa0tJQ0FnSUhCeWFXNTBLSEpsYzNWc2RITmZZWEpqYUdsMlpTa0tJQ0FnSUhCeWFXNTBLQ2QxY0d4dllXUnBibWNuS1FvZ0lDQWdjek11YldWMFlTNWpiR2xsYm5RdWRYQnNiMkZrWDJacGJHVW9jbVZ6ZFd4MGMxOWhjbU5vYVhabExDQkNWVU5MUlZSZlRrRk5SVjlQVlZRc0lHOXpMbkJoZEdndVltRnpaVzVoYldVb2NtVnpkV3gwYzE5aGNtTm9hWFpsS1NrS0lDQWdJSEJ5YVc1MEtDZDFjR3h2WVdSbFpDY3BDZ29LWkdWbUlHMWhhVzRvS1RvS0lDQWdJSE54Y3lBOUlHSnZkRzh6TG5KbGMyOTFjbU5sS0NkemNYTW5MQ0J5WldkcGIyNWZibUZ0WlQwblpYVXRZMlZ1ZEhKaGJDMHhKeWtLSUNBZ0lIUnllVG9LSUNBZ0lDQWdJQ0J4ZFdWMVpTQTlJSE54Y3k1blpYUmZjWFZsZFdWZllubGZibUZ0WlNoUmRXVjFaVTVoYldVOUozSjBjRjl4ZFdWMVpWOXpZMmhsWkhWc1pTY3BDaUFnSUNBZ0lDQWdabTl5SUcxbGMzTmhaMlVnYVc0Z2NYVmxkV1V1Y21WalpXbDJaVjl0WlhOellXZGxjeWhOWVhoT2RXMWlaWEpQWmsxbGMzTmhaMlZ6UFRFc0lGZGhhWFJVYVcxbFUyVmpiMjVrY3oweE1DazZDaUFnSUNBZ0lDQWdJQ0FnSUdKdlpIa2dQU0J0WlhOellXZGxMbUp2WkhrS0lDQWdJQ0FnSUNBZ0lDQWdiV1Z6YzJGblpTNWtaV3hsZEdVb0tRb2dJQ0FnSUNBZ0lDQWdJQ0JsZUdWamRYUmxYMnBoY2lobGVIUnlZV04wWDJwaGNsOXVZVzFsS0dKdlpIa3BLUW9nSUNBZ0lDQWdJQ0FnSUNCaWNtVmhhd29nSUNBZ1pYaGpaWEIwSUVWNFkyVndkR2x2YmlCaGN5QmxPZ29nSUNBZ0lDQWdJSEJ5YVc1MEtHVXBDZ29LYVdZZ1gxOXVZVzFsWDE4Z1BUMGdKMTlmYldGcGJsOWZKem9LSUNBZ0lHMWhhVzRvS1FvPScgfCBiYXNlNjQgLWQgLSA+IC9ob21lL2VjMi11c2VyL3J0cF9lYzJfZXhlY3V0ZS5weQpjaG1vZCA3MDAgL2hvbWUvZWMyLXVzZXIvcnRwX2VjMl9leGVjdXRlLnB5CmNob3duIGVjMi11c2VyOmVjMi11c2VyIC9ob21lL2VjMi11c2VyL3J0cF9lYzJfZXhlY3V0ZS5weQpzdSAtIGVjMi11c2VyIC1jIC9ob21lL2VjMi11c2VyL3J0cF9lYzJfZXhlY3V0ZS5weQovdXNyL3NiaW4vcG93ZXJvZmYK'
    resp = ec2.run_instances(ImageId=AMI, InstanceType='t2.micro', MinCount=1, MaxCount=1, InstanceInitiatedShutdownBehavior='terminate',  # KeyName='MyEC3Key',  # NetworkInterfaces=[{'AssociatePublicIpAddress': False, 'DeviceIndex': 0}],
                             IamInstanceProfile={'Arn': 'arn:aws:iam::978925540073:instance-profile/EC2_S3_SQS_Full'}, UserData=base64.b64decode(USER_DATA).decode('utf8'))
    return resp['Instances'][0]['InstanceId']


def lambda_handler(event, context):
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
