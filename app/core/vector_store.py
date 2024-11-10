<content>import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import asyncio
from ..utils.text_chunker import TextChunker
from .config import get_settings
from .logger import logger

settings = get_settings()

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.EMBEDDING_MODEL
        )
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        self.chunker = TextChunker()

    async def add_document(self, doc_id: str, text: str, metadata: dict):
        try:
            # Split text into chunks
            chunks = self.chunker.get_chunks_with_overlap(text)
            
            # Prepare batch data
            chunk_texts = []
            chunk_ids = []
            chunk_metadata = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_metadata_entry = {
                    **metadata,
                    **chunk["metadata"],
                    "parent_id": doc_id
                }
                
                chunk_texts.append(chunk["text"])
                chunk_ids.append(chunk_id)
                chunk_metadata.append(chunk_metadata_entry)
            
            # Batch add chunks to collection
            self.collection.add(
                documents=chunk_texts,
                metadatas=chunk_metadata,
                ids=chunk_ids
            )
            
            logger.info(f"Added document {doc_id} with {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            raise

    async def delete_document(self, doc_id: str):
        try:
            # Delete all chunks associated with the document
            self.collection.delete(
                where={"parent_id": doc_id}
            )
            logger.info(f"Deleted document {doc_id} from vector store")
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")
            raise

    async def search(self, query: str, n_results: int = 5, min_relevance_score: float = 0.7) -> Dict[str, Any]:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Get more results initially for filtering
                include=["metadatas", "documents", "distances"]
            )
            
            # Filter and process results
            processed_results = []
            seen_docs = set()
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Convert distance to similarity score (0-1)
                similarity_score = 1 - (distance / 2)  # Assuming cosine distance
                
                if similarity_score < min_relevance_score:
                    continue
                    
                parent_id = metadata["parent_id"]
                if parent_id not in seen_docs and len(processed_results) < n_results:
                    seen_docs.add(parent_id)
                    processed_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": similarity_score
                    })
            
            return {
                "results": processed_results,
                "total_chunks": len(results["documents"][0])
            }
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise

vector_store = VectorStore()</content>