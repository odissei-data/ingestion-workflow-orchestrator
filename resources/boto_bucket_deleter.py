import argparse
import boto3

parser = argparse.ArgumentParser(description="Delete an S3 bucket")
parser.add_argument('--url', type=str, dest='boto_url', help='URL of the server')
parser.add_argument('--username', type=str, dest='access_key', help='AWS access key')
parser.add_argument('--password', type=str, dest='secret_key', help='AWS secret key')
parser.add_argument('--bucket', type=str, dest='bucket_name', help='Name of the bucket')

args = parser.parse_args()

s3_client = boto3.client(
    's3',
    endpoint_url=args.boto_url,
    aws_access_key_id=args.access_key,
    aws_secret_access_key=args.secret_key
)

# Delete all objects within the bucket
try:
    response = s3_client.list_objects(Bucket=args.bucket_name)
    if 'Contents' in response:
        objects = [{'Key': obj['Key']} for obj in response['Contents']]
        response = s3_client.delete_objects(
            Bucket=args.bucket_name,
            Delete={'Objects': objects}
        )
        print(f"Deleted {len(response['Deleted'])} objects from bucket '{args.bucket_name}'.")
    else:
        print(f"No objects found in bucket '{args.bucket_name}'.")
except Exception as e:
    print(f"Error deleting objects from bucket '{args.bucket_name}': {e}")

# Delete the bucket
try:
    response = s3_client.delete_bucket(Bucket=args.bucket_name)
    print(f"Bucket '{args.bucket_name}' deleted successfully.")
except Exception as e:
    print(f"Error deleting bucket '{args.bucket_name}': {e}")
