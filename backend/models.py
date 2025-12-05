from typing import List, Optional
from pydantic import BaseModel, validator

class SourceSection(BaseModel):
    # This model might not be directly used anymore but kept for reference
    title: str
    link: Optional[str] = None
    content: str 
    filename: Optional[str] = None

class ChatbotResponse(BaseModel):
    message: str
    source_links: List[str] = [] # Default to empty list
    source_names: List[str] = [] # Changed from source_titles, default to empty list
    # source_filenames field removed

    @validator('source_links', pre=True, always=True)
    def remove_empty_links(cls, v):
        if v is None:
            return []
        # Ensure v is iterable and elements are strings before stripping
        return [link for link in v if isinstance(link, str) and link.strip()]

    @validator('source_names', pre=True, always=True)
    def remove_empty_names(cls, v):
        if v is None:
            return []
        # Ensure v is iterable and elements are strings before stripping and truncating
        MAX_CITATION_LENGTH = 30
        processed_names = []
        for name in v:
            if isinstance(name, str) and name.strip():
                # Truncate to 30 characters, adding "..." if truncated
                truncated = name.strip()
                if len(truncated) > MAX_CITATION_LENGTH:
                    truncated = truncated[:MAX_CITATION_LENGTH - 3] + "..."
                processed_names.append(truncated)
        return processed_names 