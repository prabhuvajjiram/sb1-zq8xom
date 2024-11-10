import os
import uuid
from datetime import datetime
from fastapi import UploadFile
import chromadb
from loguru import logger

class DocumentService:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("documents")
        
    async def upload_document(self, file: UploadFile):
        try:
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            # Read and process file content
            content = await file.read()
            
            # Index document in ChromaDB
            self.collection.add(
                documents=[content.decode()],
                ids=[doc_id],
                metadatas=[{
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "created_at": datetime.now().isoformat()
                }]
            )
            
            return {
                "id": doc_id,
                "filename": file.filename,
                "message": "Document uploaded successfully"
            }
        except Exception as e:
            logger.error(f"Error in document upload: {str(e)}")
            raise
            
    async def list_documents(self):
        try:
            # Get all documents from ChromaDB
            results = self.collection.get()
            
            documents = []
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                documents.append({
                    "id": doc_id,
                    "filename": metadata["filename"],
                    "created_at": metadata["created_at"],
                    "content_type": metadata["content_type"]
                })
                
            return documents
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise
            
    async def delete_document(self, document_id: str):
        try:
            self.collection.delete(ids=[document_id])
            return {"message": "Document deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise