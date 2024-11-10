from atlassian import Confluence
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

class ConfluenceIntegration:
    def __init__(self):
        self.confluence = Confluence(
            url=os.getenv('CONFLUENCE_URL'),
            username=os.getenv('CONFLUENCE_USERNAME'),
            password=os.getenv('CONFLUENCE_API_TOKEN')
        )

    def get_space_content(self, space_key: str):
        try:
            pages = self.confluence.get_all_pages_from_space(space_key, start=0, limit=500)
            return self._process_pages(pages)
        except Exception as e:
            logger.error(f"Error fetching Confluence content: {str(e)}")
            raise

    def _process_pages(self, pages):
        processed = []
        for page in pages:
            content = self.confluence.get_page_by_id(page['id'])
            attachments = self.confluence.get_attachments_from_content(page['id'])
            
            processed.append({
                'id': page['id'],
                'title': page['title'],
                'content': content['body']['storage']['value'],
                'attachments': [att['title'] for att in attachments]
            })
        return processed