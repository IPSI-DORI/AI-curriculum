from fastapi import FastAPI
from app.service.ragFunction2 import create_curriculum
from fastapi.responses import JSONResponse

app = FastAPI()

# fast api 테스트
@app.get("/api/ai/")
def root():
    return {"message": "Hello World"}


# 백터 데이터베이스 생성
@app.post("/api/ai/create_vector_db")
async def create_vector_db(platform: str):
    from app.service.ragFunction import create_all_subject_vector_db
    result = create_all_subject_vector_db(platform)
    return result

@app.delete("/api/ai/delete_vector_db")
async def delete_vector_db(platform: str):
    from app.service.ragFunction import delete_vector_db
    result = delete_vector_db(platform)
    return result

@app.post("/api/ai/crawling/ebs")
async def crawling_ebs():
    from app.service.ebsi_carriculum import crawling_ebs
    result = crawling_ebs()
    return result

@app.post("/api/ai/crawling/mega")
async def crawling_mega():
    from app.service.megastudy_carriculum import crawling_mega
    result = crawling_mega()
    return result

@app.get("/api/ai/curriculum")
async def get_curriculum(user_question: str):
    result = create_curriculum(user_question)
    return JSONResponse(result)


@app.get("/api/ai/test")
async def test():
    from app.utils.s3_utils import read_all_csv_from_s3
    csv_files = read_all_csv_from_s3()
    return {"files": [file[0] for file in csv_files]}
    
    