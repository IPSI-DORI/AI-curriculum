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
            참고 정보와 관련 없는 질문을 한다면 "올바른 질문을 해주세요" 라고 해줘.
            질문에 대한 답변은 반드시 **JSON 형식으로** 해줘.

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

    cleaned = re.sub(r"```json\n(.*?)\n```", r"\1", response, flags=re.DOTALL).strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {
            "error": "JSONDecodeError: 응답이 JSON 형식이 아닙니다.",
            "response": response,
        }

    return result
