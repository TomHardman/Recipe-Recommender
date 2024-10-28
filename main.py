from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import RecipeAgent  # Import your RecipeAgent

from langchain_core.messages import HumanMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize the RecipeAgent
agent = RecipeAgent()

# Define a request model for incoming messages
class UserMessage(BaseModel):
    content: str

# Define a response model for outgoing responses
class AgentResponse(BaseModel):
    content: str

@app.post("/send_message", response_model=AgentResponse)
async def send_message(user_message: UserMessage):
    # Invoke the agent with the user's message
    try:
        response = agent.graph.invoke({'messages': [HumanMessage(content=user_message.content)], 'tool_calls': []}, 
                                      config={'configurable': {'thread_id': 1}})
        agent_reply = response['messages'][-1].content
        print(agent_reply)
        return AgentResponse(content=agent_reply)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Agent error") from e