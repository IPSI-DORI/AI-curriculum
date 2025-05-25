from fastapi import FastAPI
from service.ragFunction2 import create_curriculum

app = FastAPI()

# fast api 테스트
@app.get("/api/ai/")
def root():
    return {"message": "Hello World"}


# 백터 데이터베이스 생성
@app.post("/api/ai/create_vector_db")
async def create_vector_db():
    from service.ragFunction import create_vector_db
    result = create_vector_db()
    return result

@app.post("/api/ai/crawling/ebs")
async def crawling_ebs():
    from service.ebsi.ebsi_carriculum import crawling_ebs
    result = crawling_ebs()
    return result

@app.get("/api/ai/curriculum")
async def get_curriculum(user_question: str):
    result = create_curriculum(user_question)
    return result