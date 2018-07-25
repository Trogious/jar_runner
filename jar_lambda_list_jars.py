import boto3
import json
import os


def response(body, status):
    resp = {"isBase64Encoded": False, "statusCode": status, "body": json.dumps(body), 'headers': {'Access-Control-Allow-Origin': '*'}}
    return resp


def get_error_resp(error):
    return response({'message': str(error)}, 500)


def get_unauthorized_resp(error):
    return response({'message': str(error)}, 401)


def handler(event, context):
    resp = get_error_resp('unknown error')
    bucket = os.getenv('JAR_LAMBDA_LIST_JARS_BUCKET')
    if bucket is None:
        resp = get_error_resp('BUCKET not provided')
    else:
        try:
            objs = []
            s3 = boto3.client('s3')
            objects = s3.list_objects(Bucket=bucket, Prefix='jars/')
            if 'Contents' in objects.keys():
                print(objects)
                for key in objects['Contents']:
                    if key['Key'].endswith('.jar'):
                        objs.append(key['Key'].replace('jars/', ''))
            resp = response({'jars': objs}, 200)
        except Exception as e:
            resp = get_error_resp(e)
    return resp
