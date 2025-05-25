# 베이스 이미지
FROM python:3.11-slim

# 작업 디렉토리 생성
WORKDIR /main

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 컨테이너 실행 시 커맨드
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
