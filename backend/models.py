from typing import List, Optional
from pydantic import BaseModel, validator

class SourceSection(BaseModel):
    title: str
    link: Optional[str] = None  # Optional link
    content: str # Added content field as it's used in retrieve_relevant_sections

class ChatbotResponse(BaseModel):
    message: str
    source_links: List[str]
    source_titles: List[str]

    @validator('source_links', pre=True, always=True) # Ensure validation runs even if list is provided
    def remove_empty_links(cls, v):
        return [link for link in v if link] # Filter out None or empty strings 