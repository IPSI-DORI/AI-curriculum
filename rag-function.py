import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

# 1. csv 읽어오기
courses_df = pd.read_csv('courses.csv')
lectures_df = pd.read_csv('lectures.csv')

# 2. 텍스트 만들기
texts = []

for idx, row in courses_df.iterrows():
    text = f"코스명: {row['title']} / 강사: {row['teacher']} / 설명: {row['description']} / 리뷰 수: {row['reviews']}"
    texts.append(text)

for idx, row in lectures_df.iterrows():
    text = f"강의명: {row['title']} / 강의 소개: {row['info']}"
    texts.append(text)

# 3. 임베딩 객체 준비
embeddings = OpenAIEmbeddings()

# 4. 벡터DB 생성 (Chroma)
db = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    persist_directory="./chroma_db"  # 로컬 저장할 경로
)

# 5. 저장
db.persist()

print("벡터 DB 구축 완료!")