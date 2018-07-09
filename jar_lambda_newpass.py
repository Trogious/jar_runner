import boto3
import json
import os


def response(body, status):
    resp = {'isBase64Encoded': False, 'statusCode': status, 'body': json.dumps(body), 'headers': {'Access-Control-Allow-Origin': '*'}}
    return resp


def get_error_resp(error):
    return response({'message': str(error)}, 500)


def get_unauthorized_resp(error):
    return response({'message': str(error)}, 401)


def get_challenge_params(body):
    if body is not None and 'password' in body.keys() and 'user' in body.keys() and ('Session' in body.keys() or 'verificationCode' in body.keys()):
        return {k: body[k] for k in body.keys()}
    return None


def lambda_handler(event, context):
    resp = get_error_resp('unknown error')
    client = boto3.client('cognito-idp')
    try:
        if event is not None and 'body' in event.keys():
            params = get_challenge_params(json.loads(event['body']))
            if params is None:
                resp = get_error_resp('challenge params not provided')
            else:
                client_id = os.getenv('RTP_LAMBDA_AUTH_CLIENT_ID')
                if client_id is None:
                    resp = get_error_resp('CLIENT_ID not provided')
                else:
                    if 'Session' in params.keys():
                        resp = client.respond_to_auth_challenge(ClientId=client_id, ChallengeName='NEW_PASSWORD_REQUIRED', Session=params['Session'], ChallengeResponses={'NEW_PASSWORD': params['password'], 'USERNAME': params['user']})
                    else:
                        resp = client.confirm_forgot_password(ClientId=client_id, ConfirmationCode=params['verificationCode'], Username=params['user'], Password=params['password'])
                    if 'AuthenticationResult' in resp.keys():
                        auth_result = resp['AuthenticationResult']
                        if 'IdToken' in auth_result.keys() and 'ExpiresIn' in auth_result.keys():
                            resp = response({'IdToken': auth_result['IdToken'], 'ExpiresIn': auth_result['ExpiresIn']}, 200)
                        else:
                            resp = get_unauthorized_resp('cannot find IdToken or ExpiresIn')
                    elif 'ResponseMetadata' in resp.keys() and resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                        resp = response({'passwordChangeSuccessful': True}, 200)
                    else:
                        resp = get_unauthorized_resp('cannot find AuthenticationResult')
    except client.exceptions.NotAuthorizedException as e:
        resp = get_unauthorized_resp('not authorized, maybe invalid user or password')
    except Exception as e:
        resp = get_error_resp(e)
    return resp
