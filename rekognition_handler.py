import boto3
import time
import json
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

# Rekognition client'ını oluştur
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

def start_label_detection(bucket_name, video_name):
    response = rekognition.start_label_detection(
        Video={'S3Object': {'Bucket': bucket_name, 'Name': video_name}}
    )
    return response['JobId']

def get_label_detection_result(job_id):
    print("AWS Rekognition sonucu bekleniyor...")
    while True:
        result = rekognition.get_label_detection(JobId=job_id)
        status = result['JobStatus']
        if status == 'SUCCEEDED':
            print("Etiketleme tamamlandı ✅")
            return result
        elif status in ['FAILED', 'ERROR']:
            raise Exception(f"İşlem başarısız: {status}")
        else:
            print("Bekleniyor... İşlem devam ediyor...")
            time.sleep(5)

def save_result_to_file(result, filename):
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)
    print(f"Etiketler {filename} dosyasına kaydedildi.")