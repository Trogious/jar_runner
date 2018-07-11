#!/bin/sh -
#yum install -y python3 java-1.8.0-openjdk.x86_64
#pip3 install boto3
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --region ${AWS::Region} --resource AMICreate
/usr/sbin/poweroff
