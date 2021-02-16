#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json, boto3
import os
import requests
import signal
import sys
from pathlib import Path


# global variables
# extension name has to match the file's parent directory name)
LAMBDA_EXTENSION_NAME = Path(__file__).parent.name

# custom class to handle interaction with S3
class S3JsonBucket:
    def __init__(self, bucket_name):
        self.bucket = boto3.resource("s3").Bucket(bucket_name)

    def read_file(self, key):
        return json.load(self.bucket.Object(key=key).get()["Body"].read().decode('utf-8'))

    def upload_file(self, key, obj):
        return self.bucket.Object(key=key).put(Body=json.dumps(obj))

# custom extension code
def execute_custom_processing(event):
    # perform custom per-event processing here
    print(f"[{LAMBDA_EXTENSION_NAME}] Received event: {json.dumps(event)}", flush=True)
    
    # TODO: write code...
    # received event
    received_event_id = event['requestId']

    # grab event payload from /tmp
    payload_body = process_result(str(received_event_id))
    data = { "event": payload_body }

    # connect to S3
    s3Bucket = S3JsonBucket("omokesexamplebucket")

    # write to S3 bucket 
    s3Bucket.upload_file(f"{received_event_id}.json", data)

# read result from file
def read_result(req_id):
    basepath = '/tmp/'
    
    print(f"[{LAMBDA_EXTENSION_NAME}] {os.path.join(basepath, req_id)}")    
    if os.path.isfile(os.path.join(basepath, req_id)):
        with open(os.path.join(basepath, req_id), 'rb') as f:
            reader = json.load(f)
            return reader

# process result from file
def process_result(req_id):
    try:
        data = read_result(req_id)
        print(f'[{LAMBDA_EXTENSION_NAME}] Received event body: {json.dumps(data)}')
        return data
    except Exception as e:
        print(f'Error processing invocation result: {e.message}')

# boiler plate code
def handle_signal(signal, frame):
    # if needed pass this signal down to child processes
    print(f"[{LAMBDA_EXTENSION_NAME}] Received signal={signal}. Exiting.", flush=True)
    sys.exit(0)


def register_extension():
    print(f"[{LAMBDA_EXTENSION_NAME}] Registering...", flush=True)
    headers = {
        'Lambda-Extension-Name': LAMBDA_EXTENSION_NAME,
    }
    payload = {
        'events': [
            'INVOKE',
            'SHUTDOWN'
        ],
    }
    response = requests.post(
        url=f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/register",
        json=payload,
        headers=headers
    )
    ext_id = response.headers['Lambda-Extension-Identifier']
    print(f"[{LAMBDA_EXTENSION_NAME}] Registered with ID: {ext_id}", flush=True)

    return ext_id


def process_events(ext_id):
    headers = {
        'Lambda-Extension-Identifier': ext_id
    }
    while True:
        print(f"[{LAMBDA_EXTENSION_NAME}] Waiting for event...", flush=True)
        response = requests.get(
            url=f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",
            headers=headers,
            timeout=None
        )
        event = json.loads(response.text)
        if event['eventType'] == 'SHUTDOWN':
            print(f"[{LAMBDA_EXTENSION_NAME}] Received SHUTDOWN event. Exiting.", flush=True)
            sys.exit(0)
        else:
            execute_custom_processing(event)


def main():
    # handle signals
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # execute extensions logic
    extension_id = register_extension()
    process_events(extension_id)


if __name__ == "__main__":
    main()

