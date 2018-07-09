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


def get_credentiale(body):
    if body is not None and 'user' in body.keys() and 'password' in body.keys():
        return (body['user'], body['password'])
    return (None, None)


def lambda_handler(event, context):
    resp = get_error_resp('unknown error')
    client = boto3.client('cognito-idp')
    try:
        if event is not None and 'body' in event.keys():
            user, password = get_credentiale(json.loads(event['body']))
            if None in [user, password]:
                resp = get_error_resp('user or password not provided')
            else:
                client_id = os.getenv('JAR_LAMBDA_AUTH_CLIENT_ID')
                if client_id is None:
                    resp = get_error_resp('CLIENT_ID not provided')
                else:
                    resp = client.initiate_auth(ClientId=client_id, AuthFlow='USER_PASSWORD_AUTH', AuthParameters={'USERNAME': user, 'PASSWORD': password})
                    if 'ChallengeName' in resp.keys() and resp['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
                        resp = response({'ChallengeName': resp['ChallengeName'], 'Session': resp['Session']}, 200)
                    elif 'AuthenticationResult' in resp.keys():
                        auth_result = resp['AuthenticationResult']
                        if 'IdToken' in auth_result.keys() and 'ExpiresIn' in auth_result.keys() and 'AccessToken' in auth_result.keys():
                            resp = response({'IdToken': auth_result['IdToken'], 'ExpiresIn': auth_result['ExpiresIn'], 'AccessToken': auth_result['AccessToken']}, 200)
                        else:
                            resp = get_unauthorized_resp('cannot find IdToken or ExpiresIn')
                    else:
                        resp = get_unauthorized_resp('cannot find AuthenticationResult')
    except client.exceptions.NotAuthorizedException as e:
        resp = get_unauthorized_resp('not authorized, maybe invalid user or password')
    except client.exceptions.UserNotFoundException as e:
        resp = get_unauthorized_resp('not authorized, maybe invalid user or password')
    except client.exceptions.PasswordResetRequiredException as e:
        resp = response({'passwordResetRequired': True}, 200)
    except Exception as e:
        resp = get_error_resp(e)
    return resp
