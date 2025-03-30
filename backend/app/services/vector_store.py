import hashlib
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.utils.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    VECTOR_DB_PATH
)

class VectorStoreService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_EMBEDDING_MODEL
        )
        self.vector_store = self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store."""
        return Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
    
    async def find_relevant_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find relevant content using ChromaDB.
        
        Args:
            query: The user's query string
            top_k: Number of results to return
            
        Returns:
            List of documents with text, id, and similarity score
        """
        results = await self.vector_store.asimilarity_search_with_score(
            query=query,
            k=top_k
        )
        
        similar_docs = []
        for doc, score in results:
            # Create a hash for the document similar to the TS implementation
            doc_hash = hashlib.sha256(doc.page_content.encode()).hexdigest()[:8]
            
            similar_docs.append({
                "text": doc.page_content,
                "id": doc_hash,
                "similarity": score,
                "metadata": doc.metadata
            })
            
        return similar_docs

# Create a singleton instance
vector_store_service = VectorStoreService()

async def generate_embedding(value: str) -> List[float]:
    """Generate embedding for a given text."""
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_EMBEDDING_MODEL
    )
    input_text = value.replace("\n", " ")
    embedding = await embeddings.aembed_query(input_text)
    return embedding
