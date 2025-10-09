import argparse
import boto3

parser = argparse.ArgumentParser(description="Download an S3 bucket")
parser.add_argument('--url', type=str, dest='boto_url', help='URL of the server')
parser.add_argument('--username', type=str, dest='access_key', help='AWS access key')
parser.add_argument('--password', type=str, dest='secret_key', help='AWS secret key')
parser.add_argument('--bucket', type=str, dest='bucket_name', help='Name of the bucket')
parser.add_argument('--directory', type=str, dest='download_directory', default=".", help='Directory to download files to')
args = parser.parse_args()

s3_client = boto3.client(
    's3',
    endpoint_url=args.boto_url,
    aws_access_key_id=args.access_key,
    aws_secret_access_key=args.secret_key
)

download_directory = args.download_directory

try: 
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=args.bucket_name,
    )
    object_count = 0
    page_count = 0
    for page in pages:
        page_count += 1
        if 'Contents' in page:
            object_count += len(page['Contents'])
            print(f"Number of objects in page '{page_count}' of bucket '{args.bucket_name}': {len(page['Contents'])}")
            print(f"Start Downloading {len(page['Contents'])} objects from bucket '{args.bucket_name}' in page {page_count}:")
            for obj in page['Contents']:
                s3_client.download_file(Bucket=args.bucket_name, Key=obj['Key'], Filename=download_directory+'/'+obj['Key'])
                print(".", end="", flush=True) # most primitive progress indicator
            print()  # for newline after progress dots 
            print(f"Downloading page {page_count} done.")
            print(f"Total number of objects downloaded so far from '{args.bucket_name}': {object_count}")
        else:
            print(f"No objects found in '{args.bucket_name}'")
    if object_count > 0:
        print(f"Downloading done. Total number of objects downloaded from '{args.bucket_name}': {object_count}")
except Exception as e:
    print(f"Error downloading objects from bucket '{args.bucket_name}': {e}")