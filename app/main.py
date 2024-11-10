from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import chromadb
import os
from datetime import datetime
from pydantic import BaseModel
import json
from loguru import logger

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB
client = chromadb.Client()
collection = client.create_collection("documents")

class ChatMessage(BaseModel):
    message: str
    context: Optional[List[str]] = []

class DocumentInfo(BaseModel):
    id: str
    name: str
    timestamp: str

@app.post("/upload")
async def upload_document(file: UploadFile):
    try:
        content = await file.read()
        doc_id = f"doc_{datetime.now().timestamp()}"
        
        # Index document in ChromaDB
        collection.add(
            documents=[content.decode()],
            metadatas=[{"name": file.filename}],
            ids=[doc_id]
        )
        
        return {"message": "Document uploaded successfully", "id": doc_id}
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    try:
        docs = collection.get()
        return [
            DocumentInfo(
                id=doc_id,
                name=metadata["name"],
                timestamp=doc_id.split("_")[1]
            )
            for doc_id, metadata in zip(docs["ids"], docs["metadatas"])
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        collection.delete(ids=[doc_id])
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        # Query relevant documents
        results = collection.query(
            query_texts=[message.message],
            n_results=3
        )
        
        # Process with context and return response
        context = results["documents"][0] if results["documents"] else []
        
        # Here you would typically call OpenAI API with the context
        # For now, returning a simple response
        return {
            "response": "This is a placeholder response. Implement OpenAI integration.",
            "context": context
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)