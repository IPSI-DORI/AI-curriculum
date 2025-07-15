import pandas as pd
import shutil
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from app.utils.s3_utils import read_all_csv_from_s3  # 사용자 환경에 맞게 유지

load_dotenv()

SUBJECT_MAP = {
    "경제": "economics",
    "국어": "korean",
    "동아시아사": "east_asian_history",
    "물리1": "physics1",
    "물리2": "physics2",
    "사회문화": "sociology",
    "생명과학1": "biology1",
    "생명과학2": "biology2",
    "생활과 윤리": "ethics_life",
    "세계사": "world_history",
    "세계지리": "world_geography",
    "수학": "math",
    "영어": "english",
    "윤리와 사상": "ethics_philosophy",
    "지구과학1": "earth_science1",
    "지구과학2": "earth_science2",
    "통합사회1": "integrated_social1",
    "통합사회1,2": "integrated_social1_2",
    "통합사회2": "integrated_social2",
    "한국사": "korean_history",
    "한국지리": "korean_geography",
    "화학1": "chemistry1",
    "화학2": "chemistry2"
}

def create_all_subject_vector_db(platform: str):
    try:
        results = []

        for subject in SUBJECT_MAP.keys():
            subject_slug = SUBJECT_MAP[subject]
            print(f"🔄 {platform} / {subject} 벡터 DB 생성 중...")

            db_dir = os.path.abspath(f"./chroma_db/{platform}_{subject_slug}")
            if os.path.exists(db_dir):
                print(f"기존 DB 디렉토리 삭제: {db_dir}")
                shutil.rmtree(db_dir)

            # S3에서 platform과 subject에 맞는 CSV만 읽기
            csv_files = read_all_csv_from_s3(platform=platform, subject=subject)
            if not csv_files:
                print(f"⚠️ {platform} / {subject}: S3 데이터 없음")
                results.append(f"{platform} / {subject}: 데이터 없음")
                continue

            courses_dfs, lectures_dfs = [], []

            for file_name, file_content in csv_files:
                if "courses" in file_name:
                    courses_dfs.append(file_content)
                elif "lectures" in file_name:
                    lectures_dfs.append(file_content)

            if not courses_dfs or not lectures_dfs:
                print(f"⚠️ {platform} / {subject}: 데이터 불완전")
                results.append(f"{platform} / {subject}: 데이터 불완전")
                continue

            courses_df = pd.concat(courses_dfs, ignore_index=True)
            lectures_df = pd.concat(lectures_dfs, ignore_index=True)

            texts, metadatas = [], []

            for _, course_row in courses_df.iterrows():
                course_id = course_row['course_id']
                course_title = course_row['title']
                teacher = course_row['teacher']
                description = course_row['description']
                subject_name = course_row['subject']
                grade = course_row['grade']
                platform_name = course_row['platform']
                is_paid = course_row['is_paid']
                price = course_row['price']
                url = course_row['url']

                related_lectures = lectures_df[lectures_df['course_id'] == course_id]
                lecture_texts = [
                    f"- {lecture_row['title']} / {lecture_row['info']}"
                    for _, lecture_row in related_lectures.iterrows()
                ]
                lectures_combined = "\n".join(lecture_texts) if lecture_texts else "강의 없음"

                full_text = f"""
                    강의 ID: {course_id}
                    과목: {subject_name}
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
                metadatas.append({"source": f"{platform}_{subject_slug}", "course_id": course_id})

            embeddings = OpenAIEmbeddings()
            db = Chroma(
                embedding_function=embeddings,
                persist_directory=db_dir,
                collection_name=f"{platform}_{subject_slug}_collection"
            )

            # 배치로 임베딩 추가
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                db.add_texts(
                    texts=texts[i:i + batch_size],
                    metadatas=metadatas[i:i + batch_size]
                )

            db.persist()
            print(f"✅ {platform} / {subject} → 총 {len(texts)}개 문서 임베딩 완료")
            results.append(f"{platform} / {subject}: {len(texts)}개 문서 임베딩 완료")

        return results

    except Exception as e:
        return f"Error occurred: {str(e)}"
