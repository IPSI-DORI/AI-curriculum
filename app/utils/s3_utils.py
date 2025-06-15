import boto3
import os
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY_ID')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION_ID')

def upload_to_s3(file_name: str):
    client = boto3.client('s3',
                        aws_access_key_id=AWS_ACCESS_KEY,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_DEFAULT_REGION
                        )

    input_file_name = file_name      # 업로드할 파일 이름 
    bucket = 'ai-ipsi'           #버켓 주소
    key = file_name # s3 파일

    client.upload_file(input_file_name, bucket, key) #파일 저장
    

def read_csv_from_s3(prefix: str=""):
    s3 = boto3.client('s3')
    bucket = 'ai-ipsi'
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    csv_files = []
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith('.csv'):
            obj_data = s3.get_object(Bucket=bucket, Key=key)
            csv_files.append((key, BytesIO(obj_data['Body'].read())))
    return csv_files