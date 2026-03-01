from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from services.rag import generate_answer
from routers.auth import get_current_user   # your dependency from auth.py
from services.database import db
from bson import ObjectId



router = APIRouter()

class ChatMessage(BaseModel):
    role: str       # "human" or "ai"
    content: str


class ChatRequest(BaseModel):
    question: str
    repo_id: str
    chat_history: list[ChatMessage] = []   

def convert_chat_history(history: list[ChatMessage]):
    messages = []
    for message in history:
        if message.role == "human":
            messages.append(HumanMessage(content=message.content))
        elif message.role == "ai":
            messages.append(AIMessage(content=message.content))
    return messages

@router.post("/query")
async def chat(request: ChatRequest, current_user = Depends(get_current_user)):
    # 1. validate repo_id belongs to user (you'll implement this)
    repo = await db.repos.find_one({
        "_id": ObjectId(request.repo_id),
        "user_id": str(current_user["_id"])
    })
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    
    converted_history = convert_chat_history(request.chat_history)  # if you want to use chat history in the future
    # 2. generate answer using RAG
    response = generate_answer(
        question=request.question,
        repo_id=request.repo_id,
        chat_history=converted_history
    )

    return response