# Lambda External Extension- Logs Event Payload-S3 Demo in Python 
This demo does not include a Lambda function. Only an extension that needs to be delivered as a Lambda Layer.

> Note: This extension requires the Python 3 runtime to be present in the Lambda execution environment of your function.

The extension uses the Extensions API to register for INVOKE and SHUTDOWN events.

This example needs a S3_BUCKET_NAME environment variable in the calling Lambda function. A Lambda function needs to be configured with an environment variable "S3_BUCKET_NAME" to specify the S3 bucket name. Lambda writes the event payload to the /tmp directory. The extension reads from the directory and copies the file to the S3 bucket. 

The Lambda function needs to have an execution role with a policy that is similar to this:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:PutLogEvents",
                "logs:CreateLogGroup",
                "logs:CreateLogStream"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::mybucket/*"
        }
    ]
}
```

For this demo purpose, I used a simple Lambda function that writes to the /tmp directory and return a 200 HTTP Code.

```
import os
import json

print('Loading function')


def lambda_handler(event, context):
    print("context requestId " + context.aws_request_id)
    write_file(event, context)
    return json.dumps({
        "status": 200
        })

     
def write_file(event, context):
    try:
        # TODO: write code...
        basepath = '/tmp/'
        if not os.path.isfile(os.path.join(basepath, context.aws_request_id)):
            with open(os.path.join(basepath, context.aws_request_id), 'w') as f:
                body = json.dumps(event, indent=4)
                f.write(body)
                f.close()
    except Exception as e:
    	print('Error processing invocation: ' + e.message)   
```

## Installation Instructions
There are two components to this sample:
* `extensions/`: This sub-directory should be extracted to /opt/extensions where the Lambda platform will scan for executables to launch extensions
* `python-extension-log-eventpayload-to-s3/`: This sub-directory should be extracted to /opt/python-extension-log-eventpayload-to-s3  which is referenced by the `extensions/python-extension-log-eventpayload-to-s3` executable and includes a Python executable along with all of its necessary dependencies.

## Prep Python Dependencies
Install the extension dependencies locally, which will be mounted along with the extension code.

```bash
$ cd python-extension-log-eventpayload-to-s3 
$ chmod +x extension.py
$ pip3 install -r requirements.txt -t .
$ cd ..
```

## Layer Setup Process
The extensions .zip file should contain a root directory called `extensions/`, where the extension executables are located and another root directory called `python-extension-log-eventpayload-to-s3 /`, where the core logic of the extension  and its dependencies are located.

Creating zip package for the extension:
```bash
$ chmod +x extensions/python-extension-log-eventpayload-to-s3 
$ zip -r extension.zip .
```

Ensure that you have aws-cli v2 for the commands below.
Publish a new layer using the `extension.zip`. The output of the following command should provide you a layer arn.
```bash
aws lambda publish-layer-version \
 --layer-name "python-extension-log-eventpayload-to-s3" \
 --region <use your region> \
 --zip-file  "fileb://extension.zip"
```
Note the LayerVersionArn that is produced in the output.
eg. `"LayerVersionArn": "arn:aws:lambda:<region>:123456789012:layer:<layerName>:1"`

Add the newly created layer version to a Python 3.8 runtime Lambda function.


## Function Invocation and Extension Execution

When invoking the function, you should now see log messages from the example extension similar to the following:
```
	2021-02-16T22:10:07.040+02:00	START RequestId: ea4764b2-363c-44b0-a47d-357fe94e8323 Version: $LATEST
	2021-02-16T22:10:07.749+02:00	python-extension-log-eventpayload-to-s3 launching extension
	2021-02-16T22:10:07.754+02:00	[python-extension-log-eventpayload-to-s3] Registering...
	2021-02-16T22:10:07.754+02:00	[python-extension-log-eventpayload-to-s3] Registered with ID: 60a37a91-143c-43c0-89e2-03ef24a96685
	2021-02-16T22:10:07.842+02:00	[python-extension-log-eventpayload-to-s3] Waiting for event...
	2021-02-16T22:10:07.843+02:00	Loading function
	2021-02-16T22:10:07.843+02:00	EXTENSION Name: python-extension-log-eventpayload-to-s3 State: Ready Events: [INVOKE,SHUTDOWN]
	2021-02-16T22:10:07.856+02:00	[python-extension-log-eventpayload-to-s3] Received event: {"eventType": "INVOKE", "deadlineMs": 1613506237843, "requestId": "ea4764b2-363c-44b0-a47d-357fe94e8323", "invokedFunctionArn": "arn:aws:lambda:us-east-1:564727993351:function:newHelloWorld", "tracing": {"type": "X-Amzn-Trace-Id", "value": "Root=1-602c269e-0d2fc47e6a2da3d448219e51;Parent=3c06727859bb8f45;Sampled=0"}}
	2021-02-16T22:10:07.856+02:00	context requestId ea4764b2-363c-44b0-a47d-357fe94e8323
	2021-02-16T22:10:07.856+02:00	value1 = value1
	2021-02-16T22:10:07.856+02:00	value2 = value2
	2021-02-16T22:10:07.856+02:00	value3 = value3
	2021-02-16T22:10:10.297+02:00	[python-extension-log-eventpayload-to-s3] /tmp/ea4764b2-363c-44b0-a47d-357fe94e8323
	2021-02-16T22:10:10.297+02:00	[python-extension-log-eventpayload-to-s3] Received event body: {"key1": "value1", "key2": "value2", "key3": "value3"}
	2021-02-16T22:10:10.297+02:00	[python-extension-log-eventpayload-to-s3] Waiting for event...
	2021-02-16T22:10:10.316+02:00	END RequestId: ea4764b2-363c-44b0-a47d-357fe94e8323
	2021-02-16T22:10:10.316+02:00	REPORT RequestId: ea4764b2-363c-44b0-a47d-357fe94e8323 Duration: 2455.92 ms Billed Duration: 2456 ms Memory Size: 128 MB Max Memory Used: 88 MB Init Duration: 812.18 ms     
```