import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

courses_df = pd.read_csv('courses.csv')
lectures_df = pd.read_csv('lectures.csv')

texts = []

for idx, course_row in courses_df.iterrows():
    course_id = course_row['course_id']
    course_title = course_row['title']
    teacher = course_row['teacher']
    description = course_row['description']
    reviews = course_row['reviews']

    # 해당 코스의 모든 강의 추출
    related_lectures = lectures_df[lectures_df['course_id'] == course_id]

    # 강의 리스트 포맷
    lecture_texts = []
    for _, lecture_row in related_lectures.iterrows():
        lecture_texts.append(f"- {lecture_row['title']} / {lecture_row['info']}")

    lectures_combined = "\n".join(lecture_texts) if lecture_texts else "강의 없음"

    # 최종 통합 텍스트
    full_text = f"""코스 아이디: {course_id}
코스명: {course_title}
강사: {teacher}
설명: {description}
리뷰 수: {reviews}

포함된 강의:
{lectures_combined}
"""
    texts.append(full_text)

embeddings = OpenAIEmbeddings()
db = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

db.persist()
print("completed")
