import os
import operator
from dotenv import load_dotenv
from typing import Annotated, TypedDict


from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain import hub

from recipe_scraper import GoodFoodScraper
from retriever_tool import create_recipe_retriever_tool
from scraper_tool import create_recipe_scraper_tool


load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")


TOOL_SYSTEM_PROMPT = (
'You are primarily an assistant for retrieving and recommending recipes. '
'You should answer questions about recipes, ingredients, cooking times, and other recipe-related questions. '
'If you are asked questions not relating to recipes, you should respond with "I am a recipe assistant and can only answer questions about recipes." '
'Given the previous context, answer the following questions as best you can. '
'If necessary you have access to a tool for recipe retrieval and a tool for scraping data from a recipe URL.\n\n'


'The recipe_retriever tool should only be used to recommend NEW recipes.\n'
'Any questions about previously retrieved recipes MUST be answered using the context provided!\n'
'Do not overload the response with recipe metadata unless specifically requested.\n'
'After retrieving an intial set of recipes, evaluate them based on your own judgement. \n'
'If necessary perform additional searches to find the best recipes by changing the query.\n\n'

'The recipe_scraper tool should be used to get more detailed data about a specific recipe, such '
'as the method required for cooking. \n\n'

'In your output always include the title of the recipe and the URL.\n'
'If asked for more recipes than the tool outputs, you can use the tool multiple times.\n\n'
)


# Create tools
gf_scraper = GoodFoodScraper()
recipe_scraper = create_recipe_scraper_tool(gf_scraper)
recipe_reriever = create_recipe_retriever_tool(5)
TOOLS = [recipe_reriever, recipe_scraper]

# Construct language model
llm = ChatOpenAI(model="gpt-4o-mini")

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class RecipeAgent:
    def __init__(self):
        self._tools = {t.name: t for t in TOOLS}
        self._tools_llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(TOOLS)

        builder = StateGraph(AgentState)
        builder.add_node('call_tools_llm', self.call_tools_llm)
        builder.add_node('invoke_tools', self.invoke_tools)
        builder.add_conditional_edges('call_tools_llm', RecipeAgent.exists_action, {'more_tools': 'invoke_tools', 'no_more_tools': END})
        builder.add_edge('invoke_tools', 'call_tools_llm')
        builder.set_entry_point('call_tools_llm')

        memory = MemorySaver()
        self.graph = builder.compile(checkpointer=memory)
    
    @staticmethod
    def exists_action(state: AgentState):
        result = state['messages'][-1]
        if len(result.tool_calls) == 0:
            return 'no_more_tools'
        return 'more_tools'
    
    def call_tools_llm(self, state: AgentState):
        messages = state['messages']
        messages = [SystemMessage(content=TOOL_SYSTEM_PROMPT)] + messages
        message = self._tools_llm.invoke(messages)
        return {'messages': [message]}
    
    def invoke_tools(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f'Calling: {t}')
            if not t['name'] in self._tools:  # check for bad tool name from LLM
                print('\n ....bad tool name....')
                result = 'bad tool name, retry'  # instruct LLM to retry if bad
            else:
                result = self._tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print('Back to the model!')
        return {'messages': results}
        

if __name__ == '__main__':
    agent = RecipeAgent()
    config = {'configurable': {'thread_id': 1}}

    while True:
        user_input = input("User: ")
        response = agent.graph.invoke({'messages': [HumanMessage(content=user_input)], 'tool_calls': []}, config=config)
        print(response['messages'][-1].content)
