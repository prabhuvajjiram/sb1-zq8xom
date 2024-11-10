from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
from ..core.vector_store import vector_store
from ..utils.document_parser import parse_document
from ..core.logger import logger
from pydantic import BaseModel

router = APIRouter()

class Document(BaseModel):
    id: str
    filename: str
    type: str

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        
        # Parse document content
        content = await parse_document(file)
        
        # Store in vector database
        await vector_store.add_document(
            doc_id=doc_id,
            text=content,
            metadata={
                "filename": file.filename,
                "type": file.content_type
            }
        )
        
        return {"id": doc_id, "message": "Document uploaded successfully"}
    
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    try:
        await vector_store.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))