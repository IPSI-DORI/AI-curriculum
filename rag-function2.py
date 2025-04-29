import os
from dotenv import load_dotenv
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

load_dotenv()

embeddings = OpenAIEmbeddings()
db = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_template("""
너는 교육 전문가야.
아래 참고 정보를 바탕으로 질문에 답해줘.

<참고 정보>
{context}

<질문>
{question}
""")

user_question = "수학 확률과 통계 강의 추천해줘"

# 5. 벡터DB에서 유사한 데이터 검색
retrieved_docs = db.similarity_search(user_question, k=3)  # 관련있는 3개 정도 가져옴

# 6. 검색된 문서들을 하나의 문자열로 합치기
context_text = "\n".join([doc.page_content for doc in retrieved_docs])

# 7. 최종 프롬프트 구성
formatted_prompt = prompt.format_messages(context=context_text, question=user_question)

# 8. LLM에게 요청
response = llm.invoke(formatted_prompt)

print(response.content)
