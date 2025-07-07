import boto3
import os
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd
import tempfile

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY_ID")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION_ID")


def upload_to_s3(file: pd.DataFrame ,file_name):
    client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )

    with tempfile.NamedTemporaryFile(mode='w+', suffix=".csv", delete=False) as tmp:
            file.to_csv(tmp.name, index=False, encoding="utf-8-sig")  # 파일을 임시로 저장
            tmp.seek(0) 
            tmp.flush()
            
    input_file_name = tmp.name  # 업로드할 파일 이름
    bucket = "ai-ipsi"  # 버켓 주소
    key = file_name  # s3 파일

    client.upload_file(input_file_name, bucket, key)  # 파일 저장


def read_all_csv_from_s3(prefix: str = "", return_df: bool = True, platform: str = None):
    client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )

    bucket = "ai-ipsi"
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    csv_files = []

    for obj in response.get("Contents", []):
        key = obj["Key"]

        # CSV만 필터링
        if not key.endswith(".csv"):
            continue

        # platform 필터링
        if platform == "mega" and "_mega" not in key:
            continue
        if platform == "ebsi" and "_mega" in key:
            continue

        obj_data = client.get_object(Bucket=bucket, Key=key)
        content = obj_data["Body"].read()
        if return_df:
            df = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
            csv_files.append((key, df))
        else:
            csv_files.append((key, BytesIO(content)))

    if not csv_files:
        raise ValueError(f"No CSV files found for platform: {platform}")

    return csv_files
