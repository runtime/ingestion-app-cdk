import os
import boto3
import base64

def handler(event, context):
    # 1. Get environment variables
    bucket_name = os.environ['BUCKET_NAME']
    instance_id = os.environ['INSTANCE_ID']  # Pass EC2 instance ID here
    target_directory = os.environ['TARGET_DIRECTORY']

    # 2. Initialize AWS SDK clients
    s3 = boto3.client('s3')
    ssm = boto3.client('ssm')

    print(f"Processing files from bucket: {bucket_name} to EC2 instance: {instance_id}")

    # 3. Process each file upload event from S3
    for record in event['Records']:
        key = record['s3']['object']['key']
        print(f"File uploaded: {key}")

        # 4. Download file content from S3
        response = s3.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read()

        # 5. Encode the content in base64
        encoded_content = base64.b64encode(content).decode('utf-8')

        # 6. Define the remote path and command
        remote_path = f"{target_directory}/{key}"
        command = f'echo "{encoded_content}" | base64 -d > {remote_path}'

        print(f"Sending file {key} to {remote_path} on EC2 instance.")

        # 7. Send command to EC2 via SSM
        try:
            response = ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
            )
            command_id = response['Command']['CommandId']
            print(f"Command sent successfully. Command ID: {command_id}")
        except Exception as e:
            print(f"Failed to send command for file {key}: {str(e)}")

    return {
        'statusCode': 200,
        'body': 'Files processed successfully'
    }
