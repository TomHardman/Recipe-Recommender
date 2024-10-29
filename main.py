from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent import RecipeAgent  # Import your RecipeAgent

from langchain_core.messages import HumanMessage, AIMessageChunk
from typing import AsyncGenerator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize the RecipeAgent
agent = RecipeAgent(streaming=True)

# Define a request model for incoming messages
class UserMessage(BaseModel):
    content: str

# Define a response model for outgoing responses
class AgentResponse(BaseModel):
    content: str

@app.post("/send_message", response_model=AgentResponse)
async def send_message(user_message: UserMessage):
    try:
        print(f'Dealing with request {user_message}')
        response = await agent.graph.ainvoke({'messages': [HumanMessage(content=user_message.content)]}, 
                                      config={'configurable': {'thread_id': 1}})
        
        agent_reply = response['messages'][-1].content
        print(f'Sending Response for request {user_message}')
        return AgentResponse(content=agent_reply)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Agent error") from e


async def langgraph_stream(message: str):
    async for chunk, _ in agent.graph.astream({'messages': [HumanMessage(content=message)]},
                                            config={'configurable': {'thread_id': 1}},
                                            stream_mode="messages"):
        
        if chunk.content and isinstance(chunk, AIMessageChunk):
            #print(chunk, end='\n', flush=True)
            formatted_chunk = chunk.content.replace('\n', '<br>')
            yield f"data: {formatted_chunk}\n\n"


@app.get("/stream")
async def stream(message: str):
    return StreamingResponse(langgraph_stream(message), media_type="text/event-stream")