import json
import os
import re
from dotenv import load_dotenv
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

load_dotenv()

def create_curriculum(get_user_question: str, retry: int = 0):
    embeddings = OpenAIEmbeddings()
    if "ebsi" in get_user_question:
        collection_tmp = "ebsi"
        persist_dir = os.path.abspath("./ebsi_chroma_db")
        print("ebsi chroma db path:", persist_dir)
    elif "mega" in get_user_question:
        collection_tmp = "mega"
        persist_dir = os.path.abspath("./mega_chroma_db")
        print("megastudy chroma db path:", persist_dir)
    db = Chroma(
    embedding_function=embeddings,
    persist_directory=persist_dir,
    collection_name=f"{collection_tmp}_collection"  # 이거 빠졌으면 절대 못 찾음
    )
    print("collection_name", db._collection.name)

    db.persist()
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_template(
        """
        당신은 AI 커리큘럼 생성 전문가입니다. 주어진 정보와 질문을 바탕으로 최적의 커리큘럼을 생성해 주세요. 
        **꼭 과목과 관련된 강의만 추천해 주세요.** 
        **반드시 조건에 맞는 강의만 3개만 추천해 주세요. 3개보다 많거나 적으면 안 됩니다.**
        그리고 **각 강의에 포함된 전체 강의 목록(lectures_list)을 빠짐없이 포함**해주세요.

        답변은 반드시 아래와 같은 JSON 형식으로 작성해 주세요.  
        설명은 description 기반으로 요약해주시고, recommend는 추천 이유를 간단하게 써 주세요.

        예시)
        {{
            "lectures": [
                {{
                    "course_id": "course_1",
                    "title": "제목",
                    "description": "설명",
                    "subject": "과목",
                    "grade": "학년",
                    "teacher": "강사명",
                    "platform": "플랫폼명",
                    "is_paid": true,
                    "price": 10000,
                    "recommend": "추천 이유",
                    "url": "https://example.com/course_1",
                    "lectures_list": [
                        {{
                            "title": "구지가/공무도하가/황조가",
                            "info": "강의시간 10:22"
                        }},
                        ...
                        // course_id에 해당하는 강의 목록 모두 포함해서 response 해주세요.
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
    
    if not retrieved_docs:
        print("검색 결과 없음 → 전체 데이터 사용")
        retrieved_docs = db.similarity_search("", k=10)
    
    context_text = "\n".join([doc.page_content for doc in retrieved_docs])
    formatted_prompt = prompt.format_messages(
        context=context_text, question=user_question
    )
    
    print("검색된 문서 개수:", len(retrieved_docs))
    for doc in retrieved_docs:
        print("문서 내용:", doc.page_content[:200])  # 일부만 출력


    print("Formatted Prompt:", formatted_prompt[0].content)  # 디버깅용 출력

    response = llm.invoke(formatted_prompt).content

    # 코드블록 제거
    import re

    # 코드블록 제거 (json, python, 기타 코드블록 모두 제거)
    clean_response = response.strip("```json\n").strip("```")

    try:
        result = json.loads(clean_response)
    except json.JSONDecodeError:
        if retry >= 2:
            print("JSON 파싱 실패:", clean_response)
            return {"error": "JSON 파싱 실패. 입력을 확인해주세요."}
        return create_curriculum(get_user_question)
    return result