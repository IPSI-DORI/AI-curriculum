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
            너는 강의를 추천해주는 교육 전문가야.  
            아래 괄호 안의 정보를 바탕으로, 조건에 맞는 강의만 추천해줘.  
            반드시 **사용자가 원하는 과목에 해당하고**, **사용자의 학년에 맞으며**, **3개 이하로만 추천**해줘.  
            정보와 관련 없는 강의는 절대 포함하지 마.  
            추천 강의는 JSON 형식으로 주고, 아래 항목을 반드시 포함해줘:
            course_id, title, description, subject, teacher, grade, platform, is_paid, price, recommend, lectures_list

            <사용자 정보>  
            %s  ← 이 자리에 네 기존 포맷으로 채워진 사용자 입력이 들어감

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

    response = llm.invoke(formatted_prompt).content

    # 코드블록 제거
    import re

    # 코드블록 제거 (json, python, 기타 코드블록 모두 제거)
    # clean_response = response.strip("```json\n").strip("```")

    try:
        result = response
    except json.JSONDecodeError:
        create_curriculum(get_user_question)
    return result
