#!/usr/bin/env python3
import boto3


def send_to_queue(queue_name, jar_name):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return queue.send_message(MessageBody='{"name":"' + jar_name + '"}')


def main():
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='rtp_queue_schedule')
    for message in queue.receive_messages(MaxNumberOfMessages=10):
        print(message.body)
        message.delete()


if __name__ == '__main__':
    main()
    #send_to_queue('rtp_queue_schedule', 'SampleGame.jar')
