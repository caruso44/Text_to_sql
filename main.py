from fastapi import FastAPI

from postgres import run_sql
from tools import generate_SQL_tool, generate_answer_tool
from rewoo_agent import RewooAgent


app = FastAPI()


@app.get("/run_query/{question}")
async def read_item(question):
    sql = generate_SQL_tool(question)
    output = run_sql(sql)
    answer = generate_answer_tool(question, str(output))
    return {"answer": answer}

@app.get("/run_query_rewoo/{question}")
async def read_item(question):
    agent = RewooAgent()
    answer = agent.invoke(question)
    return {"answer": answer}