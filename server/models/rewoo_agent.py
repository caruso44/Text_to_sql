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

from server.models.tools import generate_SQL_tool


class AgentSchema(TypedDict):
    user_input: str
    iter: int
    max_iter: int
    plan: tuple
    output : str
    chat_history: str

class RewooAgent:
    def __init__(self) -> None:
        load_dotenv() 
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        with open('config.yaml', 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        math_template : str = self.config["Rewoo_Template"]
        template = PromptTemplate(
            input_variables=['user_input', 'chat_history'],
            template=math_template
        )
        chain = {'user_input': itemgetter("user_input"), 'chat_history': itemgetter("chat_history")} | template | llm | StrOutputParser()
        self.chain = chain
        
        def plan_step(state: AgentSchema):
            user_input = state["user_input"]
            chat_history = state["chat_history"]
            iteraction = state["iter"]
            result_dict: AgentSchema = {}
            plan = self.chain.invoke({"user_input": user_input, "chat_history" : chat_history})
            plan_list = self.get_plan_list(plan)
            result_dict["user_input"] = user_input
            result_dict['plan'] = plan_list
            result_dict["iter"] = iteraction + 1
            result_dict["max_iter"] = state["max_iter"]
            result_dict["output"] = state["output"]
            result_dict["max_iter"] = state["max_iter"]
            result_dict["chat_history"] = state["chat_history"]
            return result_dict
        
        def solve_step(state: AgentSchema):
            plan_list = state["plan"]
            iteraction = state["iter"]
            question = plan_list.pop(0)
            print(question)
            result_dict : AgentSchema = {}
            try:
                ans = generate_SQL_tool(question)
                new_plan = []
                for p in plan_list:
                    new_plan.append(p.replace("#S" + str(iteraction), str(ans)))
                result_dict['plan'] = new_plan
            except Exception as e:
                print(e)
                result_dict['plan'] = []
            result_dict["output"] = ans
            result_dict["user_input"] = state["user_input"]
            result_dict["iter"] = iteraction + 1
            result_dict["max_iter"] = state["max_iter"]
            result_dict["chat_history"] = state["chat_history"]
            return result_dict

    
        def decide_next_step(state: AgentSchema):
            plan = state["plan"]
            iteration = state["iter"]
            max_iter = state["max_iter"]
            if len(plan) == 0 or iteration >= max_iter:
                return "end"
            return "solve_step"
        
        def end_func(state: AgentSchema):
            return state


        graph_builder = StateGraph(AgentSchema)
        graph_builder.add_node("plan_step", plan_step)
        graph_builder.add_node("solve_step", solve_step)
        graph_builder.add_node("end", end_func)
        graph_builder.add_conditional_edges("solve_step", decide_next_step)
        graph_builder.add_edge(START, "plan_step")
        graph_builder.add_edge("plan_step", "solve_step")
        graph_builder.add_edge("end", END)
        self.graph = graph_builder.compile()

    def get_plan_list(self, plan_string):
        questions = []
        for line in plan_string.strip().split('\n'):
            if line.startswith('#S'):
                question = line.split('=')[1].strip()
                questions.append(question)
        return questions

    def invoke(self, initial_state: AgentSchema):
        return self.graph.invoke(initial_state)
