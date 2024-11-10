<content>from typing import List
import re

class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get chunk of text
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence
            if end < len(text):
                # Look for sentence boundaries within the last 100 characters of the chunk
                last_period = text.rfind('.', start + self.chunk_size - 100, end)
                if last_period != -1:
                    end = last_period + 1
            
            # Add chunk to list
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position, accounting for overlap
            start = end - self.chunk_overlap
        
        return chunks

    def get_chunks_with_overlap(self, text: str) -> List[dict]:
        chunks = self.split_text(text)
        return [
            {
                "text": chunk,
                "metadata": {
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]</content>