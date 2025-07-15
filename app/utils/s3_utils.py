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


def upload_to_s3(file: pd.DataFrame, file_name: str):
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
    bucket = "ai-ipsi"  # 버킷 주소
    key = file_name  # S3 파일 경로

    client.upload_file(input_file_name, bucket, key)  # 파일 저장


def read_all_csv_from_s3(prefix: str = "", return_df: bool = True, platform: str = None, subject: str = None):
    """
    S3에서 CSV 파일을 읽어오는 함수
    platform: 'ebsi' 또는 'mega'
    subject: '수학', '물리1' 등 과목명 (선택)
    """
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

        # CSV 파일만 필터링
        if not key.endswith(".csv"):
            continue

        # 플랫폼 필터링
        if platform == "mega" and "_mega" not in key:
            continue
        if platform == "ebsi" and "_mega" in key:
            continue

        # 과목 필터링 (subject가 지정된 경우)
        if subject and subject not in key:
            continue

        # 파일 읽기
        obj_data = client.get_object(Bucket=bucket, Key=key)
        content = obj_data["Body"].read()
        if return_df:
            df = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
            csv_files.append((key, df))
        else:
            csv_files.append((key, BytesIO(content)))

    if not csv_files:
        print(f"⚠️ S3에 platform='{platform}', subject='{subject}' 에 맞는 CSV 파일이 없습니다. (건너뜀)")
        return []  # 에러 대신 빈 리스트 반환

    return csv_files
