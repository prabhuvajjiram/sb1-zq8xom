<content>from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import openai
from ..core.config import get_settings
from ..core.vector_store import vector_store
from ..core.logger import logger

router = APIRouter()
settings = get_settings()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
    context: Optional[List[dict]] = None

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get relevant context from vector store
        last_user_message = next(
            (msg for msg in reversed(request.messages) if msg.role == "user"),
            None
        )
        
        if not last_user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Get context with similarity scores
        search_results = await vector_store.search(
            last_user_message.content,
            n_results=3,
            min_relevance_score=0.7
        )
        
        # Prepare context string from relevant chunks
        context_chunks = []
        for result in search_results["results"]:
            context_chunks.append({
                "content": result["content"],
                "source": result["metadata"].get("filename", "Unknown"),
                "relevance": f"{result['similarity_score']:.2f}"
            })
        
        context_text = "\n\n".join([chunk["content"] for chunk in context_chunks])
        
        # Prepare messages for OpenAI
        system_message = {
            "role": "system",
            "content": f"You are a helpful assistant. Use the following context to answer the user's question:\n\n{context_text}\n\nIf the context doesn't contain relevant information, say so."
        }
        
        messages = [system_message] + [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Get completion from OpenAI
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            temperature=0.7,
        )
        
        return ChatResponse(
            response=completion.choices[0].message.content,
            context=context_chunks
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))</content>