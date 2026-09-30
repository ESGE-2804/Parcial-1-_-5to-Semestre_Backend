import os
import boto3
import uuid

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

def upload_media_to_s3(file_bytes: bytes, filename: str, content_type: str, is_video: bool) -> str:
    s3_client = get_s3_client()
    bucket_name = os.getenv("AWS_BUCKET_VIDEOS") if is_video else os.getenv("AWS_BUCKET_THUMBNAILS")
    
    unique_filename = f"{uuid.uuid4()}-{filename}"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=unique_filename,
        Body=file_bytes,
        ContentType=content_type
    )
    
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"