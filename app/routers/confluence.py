from fastapi import APIRouter, HTTPException
from typing import List
from atlassian import Confluence
from pydantic import BaseModel
from ..core.config import get_settings
from ..core.vector_store import vector_store
from ..core.logger import logger
from ..utils.text_chunker import TextChunker
from ..utils.document_parser import parse_confluence_attachments
import html2text

router = APIRouter()
settings = get_settings()
chunker = TextChunker()
html_converter = html2text.HTML2Text()
html_converter.ignore_links = False

class ConfluencePage(BaseModel):
    id: str
    title: str
    space_key: str

@router.post("/connect/{space_key}")
async def connect_confluence(space_key: str):
    try:
        confluence = Confluence(
            url=settings.CONFLUENCE_URL,
            username=settings.CONFLUENCE_USERNAME,
            password=settings.CONFLUENCE_API_TOKEN
        )
        
        # Get all pages in the space
        pages = confluence.get_all_pages_from_space(space_key, expand="body.storage")
        processed_pages = 0
        processed_attachments = 0
        
        for page in pages:
            # Convert HTML content to markdown for better text processing
            html_content = page["body"]["storage"]["value"]
            markdown_content = html_converter.handle(html_content)
            
            # Create unique ID for each page
            doc_id = f"confluence_{page['id']}"
            
            # Add page metadata to content
            content = f"""
            Title: {page['title']}
            Space: {space_key}
            URL: {confluence.url}/wiki/spaces/{space_key}/pages/{page['id']}
            
            Content:
            {markdown_content}
            """
            
            # Store page content in chunks
            chunks = chunker.get_chunks_with_overlap(content)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                await vector_store.add_document(
                    doc_id=chunk_id,
                    text=chunk["text"],
                    metadata={
                        "type": "confluence_page",
                        "title": page["title"],
                        "space_key": space_key,
                        "page_id": page["id"],
                        "chunk_info": chunk["metadata"]
                    }
                )
            
            processed_pages += 1
            
            # Process attachments
            attachments = confluence.get_attachments_from_content(page["id"])
            if attachments.get("results"):
                attachment_count = await parse_confluence_attachments(
                    confluence,
                    page["id"],
                    attachments["results"],
                    vector_store,
                    chunker
                )
                processed_attachments += attachment_count
            
            # Get child pages recursively
            child_pages = confluence.get_child_pages(page['id'])
            if child_pages:
                for child in child_pages:
                    child_content = confluence.get_page_by_id(
                        child['id'],
                        expand="body.storage"
                    )
                    child_markdown = html_converter.handle(
                        child_content["body"]["storage"]["value"]
                    )
                    
                    child_doc_id = f"confluence_{child['id']}"
                    child_content_full = f"""
                    Title: {child['title']} (Child page of {page['title']})
                    Space: {space_key}
                    URL: {confluence.url}/wiki/spaces/{space_key}/pages/{child['id']}
                    
                    Content:
                    {child_markdown}
                    """
                    
                    # Store child page content in chunks
                    child_chunks = chunker.get_chunks_with_overlap(child_content_full)
                    for i, chunk in enumerate(child_chunks):
                        chunk_id = f"{child_doc_id}_chunk_{i}"
                        await vector_store.add_document(
                            doc_id=chunk_id,
                            text=chunk["text"],
                            metadata={
                                "type": "confluence_page",
                                "title": child["title"],
                                "space_key": space_key,
                                "page_id": child["id"],
                                "parent_page_id": page["id"],
                                "chunk_info": chunk["metadata"]
                            }
                        )
                    
                    processed_pages += 1
        
        return {
            "message": f"Successfully processed {processed_pages} Confluence pages and {processed_attachments} attachments",
            "space": space_key
        }
    
    except Exception as e:
        logger.error(f"Error connecting to Confluence: {e}")
        raise HTTPException(status_code=500, detail=str(e))