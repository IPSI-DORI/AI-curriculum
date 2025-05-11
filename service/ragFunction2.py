import json
import os
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
    참고 정보와 관련 없는 질문을 한다면 "올바른 질문을 해주세요" 라고 해줘.
    아래 예시 답변의 괄호는 파라미터 값으로 인식하고 해당 값을 채워줘.

    예시 답변:

    {{
    "recommended_course": {{
        "course_id": "S20240000896",
        "title": "(코스 아이디에 해당하는 강좌명)",
        "subject": "(코스 아이디에 해당하는 과목)",
        "teacher": "(코스 아이디에 해당하는 강사)",
        "grade": "(코스 아이디에 해당하는 학년)",
        "platform": "(코스 아이디에 해당하는 플랫폼)",
        "is_paid": "(코스 아이디에 해당하는 유료 여부)",
        "price": "(코스 아이디에 해당하는 가격)",
        "difficulty_level": "(코스 아이디에 해당하는 난이도)",
        "description": "(코스 아이디에 해당하는 설명)",
        "reviews": "(course_id에 해당하는 리뷰 수수)"
    }},
    "lecture_list": [
        {{
        "title": "(recommended_course의 course_id에 해당하는 강의 명명)",
        "info": "(recommended_course의 course_id에 해당하는 강의 소개)"
        }}, {{...}},...
        // 이렇게 course_id에 해당하는 모든 강의들을 나열해줘
    ]
    }}

    <참고 정보>
    {context}

    <질문>
    {question}
    """
    )

    user_question = get_user_question

    retrieved_docs = db.similarity_search(user_question, k=3)

    context_text = "\n".join([doc.page_content for doc in retrieved_docs])

    formatted_prompt = prompt.format_messages(context=context_text, question=user_question)

    response = llm.invoke(formatted_prompt).content
    
    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        result = {
            "error": "JSONDecodeError: 응답이 JSON 형식이 아닙니다.",
            "response": response
        }

    return result
