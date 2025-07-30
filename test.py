import yaml
import json
import re 

from dotenv import load_dotenv
from operator import itemgetter
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph

from rewoo_agent import RewooAgent

load_dotenv() 

question = "Qual o produto mais vendido da categoria Electric Bikes"
initial_state = {}
initial_state["user_input"] = question
initial_state["plan"] = []
initial_state["max_iter"] = 10
initial_state["iter"] = 0
agent = RewooAgent()
answer = agent.invoke(initial_state)
print(answer['user_input'])