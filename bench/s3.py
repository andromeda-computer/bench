import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from bench.logger import logger

# Load environment variables from .env file
load_dotenv()

def get_s3():
    # S3 configuration
    s3_access_key_id = os.getenv('S3_ACCESS_KEY_ID')
    s3_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY')
    s3_endpoint_url = os.getenv('S3_ENDPOINT_URL')
    s3_bucket_name = os.getenv('S3_BUCKET_NAME')

    # Check if all required environment variables are set
    if not all([s3_access_key_id, s3_secret_access_key, s3_endpoint_url, s3_bucket_name]):
        print("S3 environment variables are not fully set. S3 operations will be skipped.")
        return None

    # Create a session using S3 credentials
    session = boto3.Session(
        aws_access_key_id=s3_access_key_id,
        aws_secret_access_key=s3_secret_access_key
    )

    # Create an S3 client using the provided endpoint
    return session.client('s3', endpoint_url=s3_endpoint_url), s3_bucket_name

def upload_file(file_name, object_name=None):
    s3_client, bucket = get_s3()
    if not s3_client:
        return

    if object_name is None:
        object_name = file_name

    try:
        s3_client.upload_file(file_name, bucket, object_name)
        logger.info(f"File '{file_name}' uploaded successfully to '{bucket}/{object_name}'")
    except ClientError as e:
        logger.error(f"Error uploading file: {e}")

def create_folder(folder_name):
    s3_client, bucket = get_s3()
    if not s3_client:
        return

    if not folder_name.endswith('/'):
        folder_name += '/'

    try:
        s3_client.put_object(Bucket=bucket, Key=folder_name)
        logger.info(f"Folder '{folder_name}' created successfully in bucket '{bucket}'")
    except ClientError as e:
        logger.error(f"Error creating folder: {e}")