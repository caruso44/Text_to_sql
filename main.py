from fastapi import FastAPI

from postgres import run_sql
from tools import generate_SQL, generate_answer


app = FastAPI()


@app.get("/items/{question}")
async def read_item(question):
    sql = generate_SQL(question)
    output = run_sql(sql)
    answer = generate_answer(question, str(output))
    return {"answer": answer}