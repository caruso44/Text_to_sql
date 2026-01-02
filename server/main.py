import yaml
from typing import Annotated
from datetime import timedelta
from uuid import UUID, uuid4
from datetime import datetime

import uvicorn
from fastapi import FastAPI, FastAPI, Response, Depends, HTTPException, status
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from .models.tools import generate_SQL_tool, generate_answer_tool
from .models.rewoo_agent import RewooAgent
from .session import SessionData, BasicVerifier
from .schemas.user import User, UserCredentials
from .schemas.security import Token
from .schemas.session import ChatMessage, SessionData
from .security import authenticate_user, create_access_token, get_password_hash, get_current_user
from .utils import get_table_data, write_table_data, run_sql, get_Chat_history, delete_table_data


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open('config_secret.yaml', 'r', encoding='utf-8') as file:
    config_secret = yaml.safe_load(file)

with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)


ACCESS_TOKEN_EXPIRE_MINUTES = config['ACCESS_TOKEN_EXPIRE_MINUTES']


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/run_query_fewshot/{question}", tags = ["LLM"])
async def Text_to_SQL_FewShot(question):
    sql = generate_SQL_tool(question)
    output = run_sql(sql, "store_info")
    answer = generate_answer_tool(question, str(output))
    return {"answer": answer}


@app.get("/run_query_rewoo/{question}", tags = ["LLM"])
async def Text_to_SQL_Rewoo(
    question : str, 
    session_id: UUID, 
    #current_user: str = Depends(get_current_user)
    ):
    agent = RewooAgent()
    chat_history = get_Chat_history(session_id)
    dict_input = {
        "user_input": question,
        "iter" : 0,
        "max_iter" : 10,
        "plan" : "",
        "output" :  "",
        "chat_history" : chat_history["messages"]
    }
    answer = agent.invoke(dict_input)
    sql = answer["output"]
    output = run_sql(sql, "store_info")
    answer = generate_answer_tool(question, str(output))
    data = ChatMessage(session_id= session_id, message = answer, question = question, timestamp = datetime.now())
    write_table_data("users", "User_Chat_History", data)
    return data



@app.delete("/delete_session/{session_id}", tags=["Session"])
async def delete_specific_session(session_id: UUID):
    res_sessions = delete_table_data("users", "Sessions", "session_id", session_id)
    res_chat = delete_table_data("users", "User_Chat_History", "session_id", session_id)

    if "error" in res_sessions or "error" in res_chat:
        return {
            "message": f"Error deleting session {session_id}",
            "details": {"sessions": res_sessions, "chat": res_chat}
        }

    return {"message": f"Deleted session {session_id}"}


@app.post("/create_session/{name}", tags = ["Session"])
async def create_session(name: str):
    session_id = uuid4()
    session = SessionData(session_id= session_id, session_name=name)
    write_table_data("users", "Sessions", session)
    return {"message": f"Created session '{name}'", "session_id": str(session_id)}


@app.get("/list_sessions", tags = ["Session"])
async def list_sessions():
    sessions = get_table_data("users", "Sessions")
    data = sessions.assign(session_id=sessions["session_id"].astype(str)).to_dict(orient="records")
    return {"sessions": data}


@app.post("/token", tags = ["Security"])
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


@app.post("/create_login", tags = ["Security"])
async def create_login(login_info : Annotated[UserCredentials, Depends()]):
    users_data = get_table_data("users", "user_info")
    if login_info.email in users_data['email']:
         raise Exception
    else:
        user_login = User(username=login_info.username, email= login_info.email, 
                          full_name=login_info.full_name, disabled= False, 
                          hashed_password= get_password_hash(login_info.password))
        write_table_data("users", "user_info", user_login)


@app.get("/users/me", tags = ["Security"])
def read_users_me(token: str = Depends(oauth2_scheme)):
    return {"token": token}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)