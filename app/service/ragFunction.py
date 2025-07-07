import pandas as pd
import shutil
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from app.utils.s3_utils import read_all_csv_from_s3 # 이 부분은 사용자 환경에 맞게 유지

load_dotenv()

def create_vector_db(platform: str):
    try:
        if platform == "ebsi":
            db_dir = os.path.abspath("./ebsi_chroma_db")
        elif platform == "mega":
            db_dir = os.path.abspath("./mega_chroma_db")
        else:
            return f"Unknown platform: {platform}"

        # 기존 DB 디렉토리가 있다면 삭제
        # if os.path.exists(db_dir):
        #     print(f"기존 DB 디렉토리 삭제: {db_dir}")
        #     shutil.rmtree(db_dir)

        # S3에서 CSV 파일 읽어오기 (이 부분은 기존 로직 유지)
        csv_files = read_all_csv_from_s3(platform=platform)
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
        metadatas = [] # 메타데이터도 텍스트와 함께 관리

        for idx, course_row in courses_df.iterrows():
            course_id = course_row['course_id']
            course_title = course_row['title']
            teacher = course_row['teacher']
            description = course_row['description']
            subject = course_row['subject']
            grade = course_row['grade']
            platform_name = course_row['platform'] # 'platform' 변수명 충돌 피하기 위해 변경
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
            full_text = f"""
                강의 ID: {course_id}
                과목: {subject}
                세부과목: {difficulty_level}
                학년: {grade}
                강의명: {course_title}
                강사: {teacher}
                설명: {description}
                플랫폼: {platform_name}
                가격: {price}
                url: {url}
                유료/무료: {"유료" if is_paid else "무료"}
                강의 리스트:
                {lectures_combined}
                """
            texts.append(full_text)
            metadatas.append({"source": "esg", "course_id": course_id}) # 메타데이터 추가 (예시로 course_id 추가)
        
        embeddings = OpenAIEmbeddings()

        # 1. 빈 Chroma DB 초기화 (persist_directory와 collection_name 지정)
        # 이 시점에는 아직 데이터가 저장되지 않습니다.
        db = Chroma(
            embedding_function=embeddings,
            persist_directory=db_dir,
            collection_name=f"{platform}_collection"
        )

        # 2. 텍스트를 배치로 나누어 추가
        batch_size = 100 # 한 번에 처리할 텍스트 문서의 수. 이 값을 조절하여 토큰 제한을 피할 수 있습니다.
                         # 각 문서의 길이가 길다면 batch_size를 더 줄여야 할 수도 있습니다.
        total_texts = len(texts)
        print(f"총 {total_texts}개의 텍스트 문서를 임베딩합니다.")

        for i in range(0, total_texts, batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            print(f"진행 중: {i}/{total_texts} - {len(batch_texts)}개 문서 배치 처리 중...")
            
            # db.add_texts()를 사용하여 배치 단위로 텍스트와 메타데이터 추가
            # 이 함수가 내부적으로 OpenAI API 호출을 관리합니다.
            db.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas
            )
            print(f"완료: {min(i + batch_size, total_texts)}/{total_texts} 문서 처리 완료.")
        
        # 모든 배치가 추가된 후 최종적으로 DB를 디스크에 저장
        db.persist()
        print("총 벡터 수:", db._collection.count()) # db._collection.count()로 실제 저장된 벡터 수 확인
        return "Vector DB created successfully"
    except Exception as e:
        return f"Error occurred: {str(e)}"

def delete_vector_db():
    try:
        db_dir = "chroma_db" # 이 부분은 실제 DB 경로와 일치하는지 확인 필요
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)
            return "Vector DB deleted successfully"
        else:
            return "Vector DB does not exist"
    except Exception as e:
        return f"Error occurred: {str(e)}"
