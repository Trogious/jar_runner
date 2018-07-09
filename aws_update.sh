#!/bin/sh -

#lambdas='rtp_lambda_auth rtp_lambda_newpass rtp_lambda_list_jars rtp_lambda_schedule'
lambdas='rtp_lambda_newpass'

for lambda in $lambdas
do
	zip -r9 $lambda.zip $lambda.py
	aws lambda update-function-code --function-name $lambda --zip-file fileb://$lambda.zip
done
