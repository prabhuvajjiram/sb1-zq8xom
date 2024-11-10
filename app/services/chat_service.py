from typing import List
import os
from openai import OpenAI
from ..models import ChatMessage
from loguru import logger

class ChatService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def process_chat(self, messages: List[ChatMessage]):
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages
            )
            
            return {"response": response.choices[0].message.content}
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            raise