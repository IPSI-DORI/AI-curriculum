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
    persist_dir = os.path.abspath("./chroma_db")
    db = Chroma(
    embedding_function=embeddings,
    persist_directory=persist_dir,
    collection_name="esg"  # 이거 빠졌으면 절대 못 찾음
    )

    db.persist()
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_template(
        """
        당신은 AI 커리큘럼 생성 전문가입니다. 사용자의 조건에 맞는 강의를 3개 추천해주세요.

        ❗❗ 주의사항:
        - 반드시 **3개만 추천**하세요. 3개보다 많거나 적으면 안 됩니다.
        - 참고정보 각 강의에 포함된 **lectures_list는 생략 없이 포함**해야 합니다.
        - 응답은 반드시 **아래 JSON 형식만으로 출력**하세요. 설명 없이 JSON만 보여주세요.
        - **코드블럭 없이, 순수 JSON**만 출력하세요.

        예시 형식:
        {{
        "lectures": [
            {{
            "course_id": "...",
            "title": "...",
            "description": "...",
            "subject": "...",
            "grade": "...",
            "teacher": "...",
            "platform": "...",
            "is_paid": true,
            "price": 10000,
            "recommend": "...",
            "url": "...",
            "lectures_list": [
                {{ "title": "...", "info": "..." }},
                ...
            ]
            }},
            ...
        ]
        }}

        <참고 정보>
        {context}

        <질문>
        {question}

        """
    )

    user_question = get_user_question

    retrieved_docs = db.similarity_search(user_question, k=10)
    context_text = "\n".join([doc.page_content for doc in retrieved_docs])
    formatted_prompt = prompt.format_messages(
        context=context_text, question=user_question
    )
    
    print("검색된 문서 개수:", len(retrieved_docs))
    for doc in retrieved_docs:
        print("문서 내용:", doc.page_content[:200])


    print("Formatted Prompt:", formatted_prompt[0].content)

    response = llm.invoke(formatted_prompt).content.strip()

    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        print("JSON 형식 오류 발생, 재시도 중...")
        if retry_count < 2:
            return create_curriculum(get_user_question, retry_count + 1)
        else:
            return {"error": "JSON 형식 오류. 최대 재시도 초과."}

