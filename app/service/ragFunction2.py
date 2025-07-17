import json
import os
import re
from dotenv import load_dotenv
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

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

def create_curriculum(get_user_question: str, retry: int = 0):
    embeddings = OpenAIEmbeddings()
    subject_slug = ""
    if "ebsi" in get_user_question:
        collection_tmp = "ebsi"
        if "국어" in get_user_question:
            subject_slug = SUBJECT_MAP["국어"]  # "korean"
            persist_dir = os.path.abspath("./chroma_db/ebsi_korean")
        elif "수학" in get_user_question:
            subject_slug = SUBJECT_MAP["수학"]  # "math"
            persist_dir = os.path.abspath("./chroma_db/ebsi_math")
        elif "영어" in get_user_question:
            subject_slug = SUBJECT_MAP["영어"]  # "english"
            persist_dir = os.path.abspath("./chroma_db/ebsi_english")
        elif "한국사" in get_user_question:
            subject_slug = SUBJECT_MAP["한국사"]  # "korean_history"
            persist_dir = os.path.abspath("./chroma_db/ebsi_korean_history")
        elif "경제" in get_user_question:
            subject_slug = SUBJECT_MAP["경제"]  # "economics"
            persist_dir = os.path.abspath("./chroma_db/ebsi_economics")
        elif "동아시아사" in get_user_question:
            subject_slug = SUBJECT_MAP["동아시아사"]  # "east_asian_history"
            persist_dir = os.path.abspath("./chroma_db/ebsi_east_asian_history")
        elif "세계사" in get_user_question:
            subject_slug = SUBJECT_MAP["세계사"]  # "world_history"
            persist_dir = os.path.abspath("./chroma_db/ebsi_world_history")
        elif "세계지리" in get_user_question:
            subject_slug = SUBJECT_MAP["세계지리"]  # "world_geography"
            persist_dir = os.path.abspath("./chroma_db/ebsi_world_geography")
        elif "한국지리" in get_user_question:
            subject_slug = SUBJECT_MAP["한국지리"]  # "korean_geography"
            persist_dir = os.path.abspath("./chroma_db/ebsi_korean_geography")
        elif "사회문화" in get_user_question:
            subject_slug = SUBJECT_MAP["사회문화"]  # "sociology"
            persist_dir = os.path.abspath("./chroma_db/ebsi_sociology")
        elif "윤리와 사상" in get_user_question:
            subject_slug = SUBJECT_MAP["윤리와 사상"]  # "ethics_philosophy"
            persist_dir = os.path.abspath("./chroma_db/ebsi_ethics_philosophy")
        elif "생활과 윤리" in get_user_question:
            subject_slug = SUBJECT_MAP["생활과 윤리"]  # "ethics_life"
            persist_dir = os.path.abspath("./chroma_db/ebsi_ethics_life")
        elif "물리1" in get_user_question:
            subject_slug = SUBJECT_MAP["물리1"]  # "physics1"
            persist_dir = os.path.abspath("./chroma_db/ebsi_physics1")
        elif "물리2" in get_user_question:
            subject_slug = SUBJECT_MAP["물리2"]  # "physics2"
            persist_dir = os.path.abspath("./chroma_db/ebsi_physics2")
        elif "화학1" in get_user_question:
            subject_slug = SUBJECT_MAP["화학1"]  # "chemistry1"
            persist_dir = os.path.abspath("./chroma_db/ebsi_chemistry1")
        elif "화학2" in get_user_question:
            subject_slug = SUBJECT_MAP["화학2"]  # "chemistry2"
            persist_dir = os.path.abspath("./chroma_db/ebsi_chemistry2")
        elif "생명과학1" in get_user_question:
            subject_slug = SUBJECT_MAP["생명과학1"]  # "biology1"
            persist_dir = os.path.abspath("./chroma_db/ebsi_biology1")
        elif "생명과학2" in get_user_question:
            subject_slug = SUBJECT_MAP["생명과학2"]  # "biology2"
            persist_dir = os.path.abspath("./chroma_db/ebsi_biology2")
        elif "지구과학1" in get_user_question:
            subject_slug = SUBJECT_MAP["지구과학1"]  # "earth_science1"
            persist_dir = os.path.abspath("./chroma_db/ebsi_earth_science1")
        elif "지구과학2" in get_user_question:
            subject_slug = SUBJECT_MAP["지구과학2"]  # "earth_science2"
            persist_dir = os.path.abspath("./chroma_db/ebsi_earth_science2")
        elif "통합사회1" in get_user_question:
            subject_slug = SUBJECT_MAP["통합사회1"]  # "integrated_social1"
            persist_dir = os.path.abspath("./chroma_db/ebsi_integrated_social1")
        elif "통합사회1,2" in get_user_question:
            subject_slug = SUBJECT_MAP["통합사회1,2"]  # "integrated_social1_2"
            persist_dir = os.path.abspath("./chroma_db/ebsi_integrated_social1_2")
        elif "통합사회2" in get_user_question:
            subject_slug = SUBJECT_MAP["통합사회2"]  # "integrated_social2"
            persist_dir = os.path.abspath("./chroma_db/ebsi_integrated_social2")
        else:
            raise ValueError("❌ 질문에서 과목명을 찾을 수 없습니다.")
            
        print("ebsi chroma db path:", persist_dir)
    elif "mega" in get_user_question:
        collection_tmp = "mega"
        if "국어" in get_user_question:
            subject_slug = SUBJECT_MAP["국어"]  # "korean"
            persist_dir = os.path.abspath("./chroma_db/mega_korean")
        elif "수학" in get_user_question:
            subject_slug = SUBJECT_MAP["수학"]  # "math"
            persist_dir = os.path.abspath("./chroma_db/mega_math")
        elif "영어" in get_user_question:
            subject_slug = SUBJECT_MAP["영어"]  # "english"
            persist_dir = os.path.abspath("./chroma_db/mega_english")
        elif "한국사" in get_user_question:
            subject_slug = SUBJECT_MAP["한국사"]  # "korean_history"
            persist_dir = os.path.abspath("./chroma_db/mega_korean_history")
        elif "경제" in get_user_question:
            subject_slug = SUBJECT_MAP["경제"]  # "economics"
            persist_dir = os.path.abspath("./chroma_db/mega_economics")
        elif "동아시아사" in get_user_question:
            subject_slug = SUBJECT_MAP["동아시아사"]  # "east_asian_history"
            persist_dir = os.path.abspath("./chroma_db/mega_east_asian_history")
        elif "세계사" in get_user_question:
            subject_slug = SUBJECT_MAP["세계사"]  # "world_history"
            persist_dir = os.path.abspath("./chroma_db/mega_world_history")
        elif "세계지리" in get_user_question:
            subject_slug = SUBJECT_MAP["세계지리"]  # "world_geography"
            persist_dir = os.path.abspath("./chroma_db/mega_world_geography")
        elif "한국지리" in get_user_question:
            subject_slug = SUBJECT_MAP["한국지리"]  # "korean_geography"
            persist_dir = os.path.abspath("./chroma_db/mega_korean_geography")
        elif "사회문화" in get_user_question:
            subject_slug = SUBJECT_MAP["사회문화"]  # "sociology"
            persist_dir = os.path.abspath("./chroma_db/mega_sociology")
        elif "윤리와 사상" in get_user_question:
            subject_slug = SUBJECT_MAP["윤리와 사상"]  # "ethics_philosophy"
            persist_dir = os.path.abspath("./chroma_db/mega_ethics_philosophy")
        elif "생활과 윤리" in get_user_question:
            subject_slug = SUBJECT_MAP["생활과 윤리"]  # "ethics_life"
            persist_dir = os.path.abspath("./chroma_db/mega_ethics_life")
        elif "물리1" in get_user_question:
            subject_slug = SUBJECT_MAP["물리1"]  # "physics1"
            persist_dir = os.path.abspath("./chroma_db/mega_physics1")
        elif "물리2" in get_user_question:
            subject_slug = SUBJECT_MAP["물리2"]  # "physics2"
            persist_dir = os.path.abspath("./chroma_db/mega_physics2")
        elif "화학1" in get_user_question:
            subject_slug = SUBJECT_MAP["화학1"]  # "chemistry1"
            persist_dir = os.path.abspath("./chroma_db/mega_chemistry1")
        elif "화학2" in get_user_question:
            subject_slug = SUBJECT_MAP["화학2"]  # "chemistry2"
            persist_dir = os.path.abspath("./chroma_db/mega_chemistry2")
        elif "생명과학1" in get_user_question:
            subject_slug = SUBJECT_MAP["생명과학1"]  # "biology1"
            persist_dir = os.path.abspath("./chroma_db/mega_biology1")
        elif "생명과학2" in get_user_question:
            subject_slug = SUBJECT_MAP["생명과학2"]  # "biology2"
            persist_dir = os.path.abspath("./chroma_db/mega_biology2")
        elif "지구과학1" in get_user_question:
            subject_slug = SUBJECT_MAP["지구과학1"]  # "earth_science1"
            persist_dir = os.path.abspath("./chroma_db/mega_earth_science1")
        elif "지구과학2" in get_user_question:
            subject_slug = SUBJECT_MAP["지구과학2"]  # "earth_science2"
            persist_dir = os.path.abspath("./chroma_db/mega_earth_science2")
        elif "통합사회1" in get_user_question:
            subject_slug = SUBJECT_MAP["통합사회1"]  # "integrated_social1"
            persist_dir = os.path.abspath("./chroma_db/mega_integrated_social1")
        elif "통합사회1,2" in get_user_question:
            subject_slug = SUBJECT_MAP["통합사회1,2"]  # "integrated_social1_2"
            persist_dir = os.path.abspath("./chroma_db/mega_integrated_social1_2")
        elif "통합사회2" in get_user_question:
            subject_slug = SUBJECT_MAP["통합사회2"]  # "integrated_social2"
            persist_dir = os.path.abspath("./chroma_db/mega_integrated_social2")
        else:
            raise ValueError("❌ 질문에서 과목명을 찾을 수 없습니다.")
            
        print("ebsi chroma db path:", persist_dir)
    db = Chroma(
    embedding_function=embeddings,
    persist_directory=persist_dir,
    collection_name=f"{collection_tmp}_{subject_slug}_collection"  # 이거 빠졌으면 절대 못 찾음
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