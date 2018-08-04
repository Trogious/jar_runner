import boto3
import datetime
import hashlib
import hmac
import logging
import os
import urllib

ENCODING = 'utf8'
SEVEN_DAYS = 604800
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def sign(key, msg):
    return hmac.new(key, msg.encode(ENCODING), hashlib.sha256).digest()


def get_signature_key(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode(ENCODING), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


def generate_presigned_s3_get(bucket, object_key, region, expires_in, access_key, secret_key):
    METHOD = 'GET'
    SERVICE = 's3'
    host = bucket + '.s3.' + region + '.amazonaws.com'
    endpoint = 'https://' + host
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d')
    canonical_uri = '/' + object_key
    canonical_headers = 'host:' + host + '\n'
    signed_headers = 'host'
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + '/' + SERVICE + '/' + 'aws4_request'
    canonical_querystring = '?X-Amz-Algorithm=AWS4-HMAC-SHA256'
    canonical_querystring += '&X-Amz-Credential=' + urllib.parse.quote_plus(access_key + '/' + credential_scope)
    canonical_querystring += '&X-Amz-Date=' + amz_date
    canonical_querystring += '&X-Amz-Expires=' + str(expires_in)
    canonical_querystring += '&X-Amz-SignedHeaders=' + signed_headers
    canonical_request = METHOD + '\n' + canonical_uri + '\n' + canonical_querystring[1:] + '\n' + canonical_headers + '\n' + signed_headers + '\nUNSIGNED-PAYLOAD'
    string_to_sign = algorithm + '\n' + amz_date + '\n' + credential_scope + '\n' + hashlib.sha256(canonical_request.encode(ENCODING)).hexdigest()
    signing_key = get_signature_key(secret_key, datestamp, region, SERVICE)
    signature = hmac.new(signing_key, (string_to_sign).encode("utf-8"), hashlib.sha256).hexdigest()
    canonical_querystring += '&X-Amz-Signature=' + signature
    url = endpoint + canonical_uri + canonical_querystring
    logger.info('presigned url: %s' % url)
    return url


def handler(event, context):
    key = event['Records'][0]['s3']['object']['key']
    access_key = os.getenv('JAR_LAMBDA_ACCESS_KEY')
    secret_key = os.getenv('JAR_LAMBDA_SECRET_KEY')
    region = os.getenv('JAR_LAMBDA_REGION')
    try:
        if None in [access_key, secret_key, region]:
            raise Exception('KEYs not set')
        url = generate_presigned_s3_get(event['Records'][0]['s3']['bucket']['name'], key, region, SEVEN_DAYS, access_key, secret_key)
        message = 'Jar execution result is now ready: ' + key + '.\n\nTo download, click here: ' + url + '\n\n\n'
        boto3.client('sns').publish(TopicArn=os.getenv('JAR_LAMBDA_NOTIFY_SNS_ARN'), Subject='JAR execution complete', Message=message)
    except Exception as e:
        logger.exception(e)
    return key
