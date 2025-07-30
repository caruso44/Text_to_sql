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

from utils import extract_sql

def generate_SQL_tool(user_input):
    load_dotenv() 
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    template_schema : str = config["SQL_generator"]
    template = PromptTemplate(
        input_variables=['user_input'],
        template=template_schema
    )
    chain =  template | llm | StrOutputParser()
    sql_string = chain.invoke({"user_input": user_input})
    sql = extract_sql(sql_string)
    return sql

def generate_answer_tool(input, output):
    load_dotenv() 
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    template_schema : str = config["answer_generator"]
    template = PromptTemplate(
        input_variables=['user_input', 'output'],
        template=template_schema
    )
    chain =  template | llm | StrOutputParser()
    print(output)
    answer = chain.invoke({"user_input": input, "output": output})
    return answer