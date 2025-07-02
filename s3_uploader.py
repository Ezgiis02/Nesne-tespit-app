import boto3
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

def upload_video_to_s3(file_path, bucket_name, s3_key):
    s3 = boto3.client('s3', 
                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                      region_name=os.getenv('AWS_REGION'))

    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"{file_path} dosyası {bucket_name}/{s3_key} olarak yüklendi.")
    
