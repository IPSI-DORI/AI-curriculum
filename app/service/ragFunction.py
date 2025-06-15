import pandas as pd
import shutil
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def create_vector_db():
    try:
        db_dir = "../../chroma_db"
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)
            
        courses_df = pd.read_csv('courses.csv')
        lectures_df = pd.read_csv('lectures.csv')

        texts = []

        for idx, course_row in courses_df.iterrows():
            course_id = course_row['course_id']
            course_title = course_row['title']
            teacher = course_row['teacher']
            description = course_row['description']
            subject = course_row['subject']
            reviews = course_row['reviews']
            grade = course_row['grade']
            platform = course_row['platform']
            is_paid = course_row['is_paid']
            price = course_row['price']
            difficulty_level = course_row['difficulty_level']

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
        과목: {subject}
        학년: {grade}
        플랫폼: {platform}
        유료 여부: {is_paid}
        가격: {price}
        난이도: {difficulty_level}

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
        return "Vector DB created successfully"
    except Exception as e:
        return f"Error occurred: {str(e)}"