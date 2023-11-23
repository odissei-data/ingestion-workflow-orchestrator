import argparse

import boto3


parser = argparse.ArgumentParser(description="Count an S3 bucket")
parser.add_argument(
    '--url', type=str, dest='boto_url',
    help='URL of the server you want to upload to'
)
parser.add_argument('--username', type=str, dest='boto_user', help='username')
parser.add_argument(
    '--password', type=str, dest='boto_password', help='password'
)
parser.add_argument(
    '--bucket', type=str, dest='bucket_name', help='Name of the bucket'
)

args = parser.parse_args()

s3_client = boto3.client(
    's3',
    endpoint_url=args.boto_url,
    aws_access_key_id=args.boto_user,
    aws_secret_access_key=args.boto_password
)

try:
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=args.bucket_name,
    )
    object_count = 0
    for page in pages:
        if 'Contents' in page:
            object_count += len(page['Contents'])
            print(f"Number of objects in '{args.bucket_name}': {object_count}")
        else:
            print(f"No objects found in '{args.bucket_name}'")

except Exception as e:
    print(f"Error: {e}")

