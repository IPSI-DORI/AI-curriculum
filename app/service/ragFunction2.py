import json
import os
import re
from dotenv import load_dotenv
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

load_dotenv()

def create_curriculum(get_user_question: str):
    embeddings = OpenAIEmbeddings()
    db = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")

    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_template(
        """
            너는 교육 전문가야.
            아래 참고 정보를 바탕으로 질문에 답해줘.
            강의를 추천받고자 하는 사람에게 강의랑 해당 강의 목록 정보를 주면 되.
            질문에 대한 답변은 반드시 **JSON 형식으로** 해줘.
            해당 course_id에 대한 모든 정보는 반드시 포함하여 전달해주고 컬럼명은
            'course_id', 'title', 'description', 'subject', 'tacher', 'grade', 'platform', 'is_paid',
            'price', 'recommend', 'lectures_list' 로 채워서 줄래? recommend는 추천 이유를 간단히 만들어서
            채워줘.

            <참고 정보>
            {context}

            <질문>
            {question}
            """
    )

    user_question = get_user_question

    retrieved_docs = db.similarity_search(user_question, k=3)
    context_text = "\n".join([doc.page_content for doc in retrieved_docs])
    formatted_prompt = prompt.format_messages(
        context=context_text, question=user_question
    )

    response = llm.invoke(formatted_prompt).content

    # 코드블록 제거
    import re

# 코드블록 제거 (json, python, 기타 코드블록 모두 제거)
    # cleaned = re.sub(r"^```[a-zA-Z]*\n([\s\S]*?)\n```$", r"\1", response.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"^```(?:json)?\n(.*)\n```$", r"\1", response.strip(), flags=re.DOTALL)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {
            "error": "JSONDecodeError: 응답이 JSON 형식이 아닙니다.",
            "response": response,
        }
        return result

    # --- CSV 참고해서 항상 동일한 구조로 반환 ---
    # 1. 추천 course_id 추출
    course_id = None
    if "recommended_course" in result and "course_id" in result["recommended_course"]:
        course_id = result["recommended_course"]["course_id"]
    elif "course_id" in result:
        course_id = result["course_id"]

    if not course_id:
        return {"error": "추천 강좌를 찾을 수 없습니다.", "response": response}

    # 2. courses.csv, lectures.csv 읽기
    courses_df = pd.read_csv("courses.csv")
    lectures_df = pd.read_csv("lectures.csv")

    # 3. 강좌 정보 찾기
    course_row = courses_df[courses_df["course_id"] == course_id]
    if course_row.empty:
        return {"error": f"course_id {course_id} not found in courses.csv"}

    course_row = course_row.iloc[0]
    recommended_course = {
        "course_id": course_row["course_id"],
        "title": course_row["title"],
        "description": course_row.get("description", ""),
        "subject": course_row.get("subject", ""),
        "teacher": course_row.get("teacher", ""),
        "grade": course_row.get("grade", ""),
        "platform": course_row.get("platform", ""),
        "is_paid": bool(course_row.get("is_paid", False)),
        "price": int(course_row.get("price", 0)),
        "recommend": result["recommended_course"].get("recommend", "") if "recommended_course" in result else ""
    }

    # 4. 강의 목록 정보 찾기
    lectures = lectures_df[lectures_df["course_id"] == course_id]
    lecture_list = []
    for _, row in lectures.iterrows():
        lecture_list.append({
            "title": row["title"],
            "info": row["info"]
        })

    return {
        "recommended_course": recommended_course,
        "lecture_list": lecture_list
    }