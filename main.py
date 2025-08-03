import yaml
from typing import Annotated
from datetime import timedelta
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, FastAPI, Response, Depends, HTTPException, status
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi.security import OAuth2PasswordRequestForm

from models.tools import generate_SQL_tool, generate_answer_tool
from models.rewoo_agent import RewooAgent
from session import SessionData, BasicVerifier
from schemas.user import User, UserCredentials
from schemas.security import Token
from security import authenticate_user, create_access_token, get_password_hash
from utils import get_table_data, write_table_data, run_sql


app = FastAPI()

cookie_params = CookieParameters()
user_sessions: dict[str, list[UUID]] = {}
with open('config_secret.yaml', 'r', encoding='utf-8') as file:
    config_secret = yaml.safe_load(file)

with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)


ACCESS_TOKEN_EXPIRE_MINUTES = config['ACCESS_TOKEN_EXPIRE_MINUTES']

cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key=config_secret['COOKIE_SECRET_KEY'],
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
    output = run_sql(sql, "store_info")
    answer = generate_answer_tool(question, str(output))
    return {"answer": answer}

@app.get("/run_query_rewoo/{question}")
async def read_item(question):
    agent = RewooAgent()
    dict_input = {
        "user_input": question,
        "iter" : 0,
        "max_iter" : 10,
        "plan" : ""
    }
    answer = agent.invoke(dict_input)
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


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.post("/create_login")
async def create_login(
    login_info : Annotated[UserCredentials, Depends()] 
):
    users_data = get_table_data("users", "user_info")
    if login_info.email in users_data['email']:
         raise Exception
    else:
        user_login = User(username=login_info.username, email= login_info.email, 
                          full_name=login_info.full_name, disabled= False, 
                          hashed_password= get_password_hash(login_info.password))
        write_table_data("users", "user_info", user_login)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)