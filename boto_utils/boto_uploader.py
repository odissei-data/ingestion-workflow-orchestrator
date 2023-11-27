import argparse
import os

import boto3

parser = argparse.ArgumentParser(
    description="Upload files to a specified s3 bucket"
)
parser.add_argument(
    '--url', type=str, dest='boto_url',
    help='URL of the server you want to upload to'
)
parser.add_argument('--username', type=str, dest='boto_user', help='username')
parser.add_argument(
    '--password', type=str, dest='boto_password', help='password'
)
parser.add_argument(
    '--path', type=str, dest='path',
    help='Path to where the data you want to upload lives'
)
parser.add_argument(
    '--bucket', type=str, dest='boto_bucket', help='Name of the bucket'
)

args = parser.parse_args()
bucket_name = args.boto_bucket

minio_client = boto3.client(
    's3',
    endpoint_url=args.boto_url,
    aws_access_key_id=args.boto_user,
    aws_secret_access_key=args.boto_password
)

print(f'Try to create bucket {bucket_name}')
try:
    minio_client.create_bucket(Bucket=bucket_name)
    print('Bucket created.')
except Exception as e:
    print(e)

for root, dirs, files in os.walk(args.path):
    for file in files:
        if not file.startswith('.DS_Store'):
            local_path = os.path.join(root, file)
            minio_client.upload_file(local_path, bucket_name, file)
            print(f'Uploaded {file}')

print('Upload completed')
