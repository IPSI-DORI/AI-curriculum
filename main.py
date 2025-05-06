from fastapi import FastAPI
from service.ragFunction2 import create_curriculum

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/ai/curriculum")
async def get_curriculum(user_question: str):
    result = create_curriculum(user_question)
    return result
