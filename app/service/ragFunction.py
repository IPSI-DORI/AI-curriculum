import pandas as pd
import shutil
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from app.utils.s3_utils import read_all_csv_from_s3

load_dotenv()

def create_vector_db():
    try:
        db_dir = "../../chroma_db"
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)
            
        csv_files = read_all_csv_from_s3()
        courses_dfs = []
        lectures_dfs = []
        
        for file_name, file_content in csv_files:
            if "courses" in file_name:
                courses_dfs.append(file_content)
            elif "lectures" in file_name:
                lectures_dfs.append(file_content)  
            
        courses_df = pd.concat(courses_dfs, ignore_index=True)
        lectures_df = pd.concat(lectures_dfs, ignore_index=True)
        
        texts = []

        for idx, course_row in courses_df.iterrows():
            course_id = course_row['course_id']
            course_title = course_row['title']
            teacher = course_row['teacher']
            description = course_row['description']
            subject = course_row['subject']
            grade = course_row['grade']
            platform = course_row['platform']
            is_paid = course_row['is_paid']
            price = course_row['price']
            difficulty_level = course_row['dificulty_level']
            url = course_row['url']
            
            # 해당 코스의 모든 강의 추출
            related_lectures = lectures_df[lectures_df['course_id'] == course_id]

            # 강의 리스트 포맷
            lecture_texts = []
            for _, lecture_row in related_lectures.iterrows():
                lecture_texts.append(f"- {lecture_row['title']} / {lecture_row['info']}")

            lectures_combined = "\n".join(lecture_texts) if lecture_texts else "강의 없음"

            # 최종 통합 텍스트
            full_text = f"""course_id: {course_id}
        title: {course_title}
        teacher: {teacher}
        description: {description}
        subject: {subject}
        grade: {grade}
        platform: {platform}
        is_paid: {is_paid}
        price: {price}
        difficulty_level: {difficulty_level}
        url: {url}

        lectures_list:
        {lectures_combined}
        """
            texts.append(full_text)

        embeddings = OpenAIEmbeddings()
        db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            persist_directory="./chroma_db",
            collection_name="esg",
            metadatas=[{"source": "esg"}] * len(texts)
        )

        db.persist()
        print("총 벡터 수:", len(texts))
        return "Vector DB created successfully"
    except Exception as e:
        return f"Error occurred: {str(e)}"
    
def delete_vector_db():
    try:
        db_dir = "chroma_db"
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)
            return "Vector DB deleted successfully"
        else:
            return "Vector DB does not exist"
    except Exception as e:
        return f"Error occurred: {str(e)}"