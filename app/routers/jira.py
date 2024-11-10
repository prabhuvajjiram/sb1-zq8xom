from fastapi import APIRouter, HTTPException, Depends
from typing import List
from atlassian import Jira
from pydantic import BaseModel
from ..core.config import get_settings
from ..core.vector_store import vector_store
from ..core.logger import logger
from ..utils.text_chunker import TextChunker

router = APIRouter()
settings = get_settings()
chunker = TextChunker()

class JiraIssue(BaseModel):
    key: str
    summary: str
    description: str
    status: str

@router.post("/connect/{project_key}")
async def connect_jira(project_key: str):
    try:
        jira = Jira(
            url=settings.JIRA_URL,
            username=settings.JIRA_USERNAME,
            password=settings.JIRA_API_TOKEN
        )
        
        # Get all issues for the project including subtasks
        jql = f"project = {project_key} ORDER BY created DESC"
        issues = jira.jql(jql, fields=["summary", "description", "status", "issuetype", "parent", "subtasks"])
        
        processed_count = 0
        for issue in issues["issues"]:
            # Create unique ID for each issue
            doc_id = f"jira_{issue['key']}"
            
            # Combine issue data
            content = f"""
            Issue Key: {issue['key']}
            Type: {issue['fields']['issuetype']['name']}
            Summary: {issue['fields']['summary']}
            Description: {issue['fields'].get('description', 'No description')}
            Status: {issue['fields']['status']['name']}
            """
            
            # Add parent information if it exists
            if 'parent' in issue['fields']:
                content += f"\nParent Issue: {issue['fields']['parent']['key']} - {issue['fields']['parent']['fields']['summary']}"
            
            # Add subtasks if they exist
            if issue['fields'].get('subtasks'):
                content += "\nSubtasks:"
                for subtask in issue['fields']['subtasks']:
                    content += f"\n- {subtask['key']}: {subtask['fields']['summary']}"
            
            # Store in vector database with chunks
            chunks = chunker.get_chunks_with_overlap(content)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                await vector_store.add_document(
                    doc_id=chunk_id,
                    text=chunk["text"],
                    metadata={
                        "type": "jira_issue",
                        "key": issue["key"],
                        "project": project_key,
                        "chunk_info": chunk["metadata"]
                    }
                )
            
            processed_count += 1
        
        return {
            "message": f"Successfully indexed {processed_count} Jira issues",
            "project": project_key
        }
    
    except Exception as e:
        logger.error(f"Error connecting to Jira: {e}")
        raise HTTPException(status_code=500, detail=str(e))