from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    JIRA_URL: str = os.getenv("JIRA_URL")
    JIRA_USERNAME: str = os.getenv("JIRA_USERNAME")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN")
    CONFLUENCE_URL: str = os.getenv("CONFLUENCE_URL")
    CONFLUENCE_USERNAME: str = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN: str = os.getenv("CONFLUENCE_API_TOKEN")
    CHROMA_PERSIST_DIR: str = "chroma_db"
    MODEL_NAME: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

@lru_cache()
def get_settings():
    return Settings()