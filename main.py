from fastapi import FastAPI

from postgres import run_sql
from tools import generate_SQL


app = FastAPI()


@app.get("/items/{question}")
async def read_item(question):
    sql = generate_SQL(question)
    output = run_sql(sql)
    return {"output": output}