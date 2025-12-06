from typing import List, Optional
from pydantic import BaseModel, validator

class SourceSection(BaseModel):
    # This model might not be directly used anymore but kept for reference
    title: str
    link: Optional[str] = None
    content: str 
    filename: Optional[str] = None

class ClarifyingOption(BaseModel):
    """A single option in a clarifying question"""
    id: str  # e.g., "A", "B", "C"
    text: str  # The option text

class ChatbotResponse(BaseModel):
    message: str
    source_links: List[str] = []  # Default to empty list
    source_names: List[str] = []  # Changed from source_titles, default to empty list
    # Clarifying question fields
    needs_clarification: bool = False  # Whether the agent needs more info
    clarifying_question: Optional[str] = None  # The question to ask the user
    clarifying_options: List[ClarifyingOption] = []  # Multiple choice options
    # Relevant docs for caching (used for follow-up questions)
    relevant_docs: List[str] = []  # Filenames of relevant documents found

    @validator('source_links', pre=True, always=True)
    def remove_empty_links(cls, v):
        if v is None:
            return []
        # Ensure v is iterable and elements are strings before stripping
        # Also limit to max 4 sources
        links = [link for link in v if isinstance(link, str) and link.strip()]
        return links[:4]  # MAX 4 sources

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
        return processed_names[:4]  # MAX 4 sources