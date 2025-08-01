import yaml

from fastapi import FastAPI, FastAPI, Response, Depends, HTTPException
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters

from postgres import run_sql
from tools import generate_SQL_tool, generate_answer_tool
from rewoo_agent import RewooAgent
from session import SessionData, BasicVerifier
from uuid import UUID, uuid4


app = FastAPI()
cookie_params = CookieParameters()
user_sessions: dict[str, list[UUID]] = {}

with open('config_secret.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key=config['COOKIE_SECRET_KEY'],
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


@app.get("/run_query/{question}")
async def read_item(question):
    sql = generate_SQL_tool(question)
    output = run_sql(sql)
    answer = generate_answer_tool(question, str(output))
    return {"answer": answer}

@app.get("/run_query_rewoo/{question}")
async def read_item(
    question,
    session_data: SessionData = Depends(verifier)
                    ):
    agent = RewooAgent()
    answer = agent.invoke(question)
    return {"answer": answer}


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@app.delete("/delete_session/{session_id}")
async def delete_specific_session(session_id: UUID, response: Response):
    session_data = await backend.read(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    await backend.delete(session_id)

    cookie.delete_from_response(response)

    return {"message": f"Deleted session {session_id}"}


@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):
    session_id = uuid4()
    data = SessionData(session_name=name)

    await backend.create(session_id, data)
    cookie.attach_to_response(response, session_id)

    if name not in user_sessions:
        user_sessions[name] = []
    user_sessions[name].append(session_id)

    return {"message": f"Created session '{name}'", "session_id": str(session_id)}

@app.get("/list_sessions/{name}")
async def list_sessions(name: str):
    sessions = user_sessions.get(name, [])
    return {"sessions": [str(sid) for sid in sessions]}

@app.post("/switch_session/{session_id}")
async def switch_session(session_id: UUID, response: Response):
    session_data = await backend.read(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Session ID not found")

    cookie.attach_to_response(response, session_id)
    return {"message": f"Switched to session '{session_data.session_name}'", "session_id": str(session_id)}