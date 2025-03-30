# Rewriting the TypeScript Backend to Python with LangChain and OpenAI

This document provides a step-by-step guide for rewriting the current TypeScript backend to a Python implementation using FastAPI, LangChain, and a vector database, replacing Azure services with direct OpenAI API integration.

## Table of Contents
1. [Current Architecture Overview](#current-architecture-overview)
2. [Approach Considerations](#approach-considerations)
3. [Python Backend Setup](#python-backend-setup)
4. [Environment Configuration](#environment-configuration)
5. [Vector Database Setup](#vector-database-setup)
6. [LangChain Integration](#langchain-integration)
7. [API Implementation](#api-implementation)
8. [Testing and Validation](#testing-and-validation)
9. [Frontend Integration](#frontend-integration)

## Current Architecture Overview

The current system uses:
- **Azure OpenAI** for chat completion
- **Azure AI Search** for semantic/vector search
- **Vercel AI SDK** for streaming responses
- **Next.js API routes** for the backend API

The main functionality includes:
- A chat endpoint that streams responses from Azure OpenAI
- A custom tool for retrieving relevant content from a knowledge base
- Vector search capabilities for finding semantic matches to user queries
- Citation tracking for referenced content

## Approach Considerations

### Why Move to FastAPI and Python

We'll move to a Python backend with FastAPI for several reasons:
- **Python ecosystem**: Python has a more mature ecosystem for AI/ML applications
- **LangChain support**: Better support and more features in the Python version of LangChain
- **Simplified implementation**: More direct approach to implementing vector search and LLM tools
- **Performance**: FastAPI offers high performance for API applications
- **Async support**: Native support for asynchronous operations similar to Next.js

### Moving from Azure to OpenAI

Advantages of using direct OpenAI APIs:
- **Simplified setup**: No need for Azure subscription and resource configuration
- **Latest models**: Direct access to the latest OpenAI models as they're released
- **Cost transparency**: Straightforward pricing without Azure overhead
- **Reduced complexity**: Fewer service dependencies to manage

## Python Backend Setup

### Step 1: Choose a Web Framework

We'll use **FastAPI** for our Python backend because:
- It provides asynchronous support, similar to Next.js
- It has built-in streaming response capabilities
- It offers automatic OpenAPI documentation
- It's lightweight and performant

```bash
pip install fastapi uvicorn
```

### Step 2: Project Structure

Create the following directory structure:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── routes/
│   │   ├── __init__.py
│   │   └── chat.py       # Chat endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai.py         # AI model integration
│   │   └── vector_store.py  # Vector database integration
│   └── utils/
│       ├── __init__.py
│       └── config.py     # Configuration utilities
├── requirements.txt
└── .env
```

## Environment Configuration

### Step 1: Required Environment Variables

Create a `.env` file with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview  # or another model of your choice
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector DB configuration
VECTOR_DB_TYPE=chroma  # or another vector DB of your choice
VECTOR_DB_PATH=./vector_db  # For local ChromaDB
```

### Step 2: Environment Variable Loading

```python
# app/utils/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Vector DB Configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")
VECTOR_DB_CONNECTION_STRING = os.getenv("VECTOR_DB_CONNECTION_STRING")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
```

## Vector Database Setup

We'll implement ChromaDB as our default vector database due to its simplicity and ability to run locally.

### Step 1: Install Vector Database Dependencies

```bash
pip install langchain langchain-openai python-dotenv
pip install langchain-chroma chromadb
```

### Step 2: Vector Store Implementation

```python
# app/services/vector_store.py
import hashlib
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.utils.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    VECTOR_DB_TYPE,
    VECTOR_DB_CONNECTION_STRING,
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
        """Initialize the vector store based on configuration."""
        if VECTOR_DB_TYPE.lower() == "chroma":
            from langchain_chroma import Chroma
            return Chroma(
                persist_directory=VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
        elif VECTOR_DB_TYPE.lower() == "pinecone":
            from langchain_pinecone import Pinecone
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(api_key=VECTOR_DB_CONNECTION_STRING)
            
            return Pinecone.from_existing_index(
                index_name="your-index-name",
                embedding=self.embeddings
            )
        elif VECTOR_DB_TYPE.lower() == "qdrant":
            from langchain_qdrant import Qdrant
            
            return Qdrant(
                url=VECTOR_DB_CONNECTION_STRING,
                collection_name="your-collection-name",
                embedding_function=self.embeddings
            )
        else:
            # Default to Chroma if no valid type is specified
            from langchain_chroma import Chroma
            return Chroma(
                persist_directory=VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
    
    async def find_relevant_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find relevant content similar to the current implementation's findRelevantContent function.
        
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
            doc_hash = hashlib.sha256(doc.page_content.encode()).digest()
            doc_id = doc_hash.hex()[:8]
            
            similar_docs.append({
                "text": doc.page_content,
                "id": doc_id,
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
```

## LangChain Integration

### Step 1: AI Service Implementation

```python
# app/services/ai.py
from typing import List, Dict, Any, AsyncGenerator, Optional
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain.agents import create_openai_tools_agent
from langchain.agents import AgentExecutor

from app.utils.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL
)
from app.services.vector_store import vector_store_service

class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0,
            streaming=True
        )
        
        # Define tools similar to the TypeScript implementation
        self.tools = [
            StructuredTool.from_function(
                func=self._get_information,
                name="getInformation",
                description="Get information from your knowledge base to answer the user's question.",
                args_schema={
                    "question": str,
                    "similarQuestions": List[str]
                },
                return_direct=True
            )
        ]
        
        # Create system message
        self.system_message = """You are a helpful assistant acting as the users' second brain.
        Use tools on every request.
        Be sure to getInformation from your knowledge base before answering any questions.
        If a response requires multiple tools, call one tool after another without responding to the user.
        If a response requires information from an additional tool to generate a response, call the appropriate tools in order before responding to the user.
        ONLY respond to questions using information from tool calls.
        If no relevant information is found in the tool calls and information fetched from the knowledge base, respond, "Sorry, I don't know."
        Be sure to adhere to any instructions in tool calls ie. if they say to respond like "...", do exactly that.
        Keep responses short and concise. Answer in a single sentence where possible.
        If you are unsure, use the getInformation tool and you can use common sense to reason based on the information you do have.
        Use your abilities as a reasoning machine to answer questions based on the information you do have.

        Cite the sources using source ids at the end of the answer text, like 【234d987】, using the id of the source.

        Respond "Sorry, I don't know." if you are unable to answer the question using the information provided by the tools.
        """
        
        # Create the agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=4  # Equivalent to maxToolRoundtrips in TS
        )
    
    async def _get_information(self, question: str, similarQuestions: List[str]) -> List[Dict[str, Any]]:
        """
        Tool implementation to get information from knowledge base.
        Similar to the getInformation tool in the TypeScript implementation.
        """
        results = []
        for query in similarQuestions:
            docs = await vector_store_service.find_relevant_content(query)
            results.extend(docs)
            
        # Remove duplicates (just like in the TS implementation)
        unique_results = {}
        for doc in results:
            if doc["text"] not in unique_results:
                unique_results[doc["text"]] = doc
                
        return list(unique_results.values())
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response to the user's messages.
        
        Args:
            messages: List of message objects with role and content
            
        Yields:
            Chunks of the generated response for streaming
        """
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
                
        # Create a streaming response
        response_stream = await self.agent_executor.astream_log(
            {"input": langchain_messages[-1].content if langchain_messages else "", 
             "chat_history": langchain_messages[:-1] if len(langchain_messages) > 1 else []}
        )
        
        # Stream the response chunks
        async for chunk in response_stream:
            if "actions" in chunk:
                # This is a tool call
                yield json.dumps({"type": "tool_call", "tool": chunk["actions"][0].tool})
            elif "steps" in chunk and chunk["steps"][-1].action_log and "output" in chunk["steps"][-1].action_log:
                # This is a tool response
                continue  # We don't need to stream this
            elif "output" in chunk:
                # This is the final answer
                yield chunk["output"]

# Create a singleton instance
ai_service = AIService()
```

## API Implementation

### Step 1: FastAPI Chat Route

```python
# app/routes/chat.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import Dict, List, Any

from app.services.ai import ai_service

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        async def stream_response():
            try:
                async for chunk in ai_service.generate_response(messages):
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            except Exception as e:
                error_message = f"data: {json.dumps({'error': str(e)})}\n\n"
                yield error_message
            finally:
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
```

### Step 2: Main FastAPI Application

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router

app = FastAPI(title="AI Chat Backend")

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes
app.include_router(chat_router, prefix="/api", tags=["chat"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

## Testing and Validation

### Step 1: Create Requirements File

```
# requirements.txt
fastapi>=0.103.1
uvicorn>=0.23.2
langchain>=0.0.335
langchain-openai>=0.0.2
langchain-chroma>=0.0.1
chromadb>=0.4.18
python-dotenv>=1.0.0
pydantic>=2.4.2
```

### Step 2: Run the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.main
```

### Step 3: Test API with curl

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What can you tell me about AI?"}]}'
```

## Frontend Integration

Since we're moving from Next.js to a separate FastAPI backend, the frontend will need some adjustments to communicate with the new API.

### Step 1: Update API Client

The frontend currently uses the Vercel AI SDK. We'll need to modify it to use the new FastAPI endpoint.

```typescript
// client-side update to point to the new backend
import { createChat } from 'ai';

// Current implementation with Vercel AI SDK
const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();

// New implementation with custom API endpoint
const { messages, input, handleInputChange, handleSubmit, isLoading } = createChat({
  api: 'http://localhost:8000/api/chat', // Update with your FastAPI URL
  headers: {
    'Content-Type': 'application/json',
  },
  // Other options remain the same
  onError: (error) => {
    console.error("API Error:", error);
    // Handle error appropriately
  },
});
```

### Step 2: CORS Configuration

Ensure the FastAPI backend allows requests from the frontend origin by updating the CORS configuration:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Data Migration from Azure AI Search

To migrate data from Azure AI Search to ChromaDB:

### Step 1: Export Data from Azure

```python
# scripts/export_from_azure.py
import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def export_from_azure():
    # Azure Search configuration
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    api_key = os.getenv("AZURE_SEARCH_KEY")
    
    if not all([endpoint, index_name, api_key]):
        print("Missing Azure Search configuration. Please check your .env file.")
        return
    
    # Initialize search client
    search_client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(api_key)
    )
    
    # Retrieve all documents
    results = []
    search_results = search_client.search("*", top=1000)
    
    for result in search_results:
        results.append(result)
    
    # Save results to a file
    with open('azure_search_export.json', 'w') as f:
        json.dump(results, f, default=str)
    
    print(f"Exported {len(results)} documents to azure_search_export.json")

if __name__ == "__main__":
    import asyncio
    asyncio.run(export_from_azure())
```

### Step 2: Import to ChromaDB

```python
# scripts/import_to_chroma.py
import os
import json
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def import_to_chroma():
    # Load the exported documents
    with open('azure_search_export.json', 'r') as f:
        exported_data = json.load(f)
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    
    # Initialize vector store
    vector_store = Chroma(
        persist_directory=os.getenv("VECTOR_DB_PATH", "./vector_db"),
        embedding_function=embeddings
    )
    
    # Process documents
    documents = []
    content_field = os.getenv("AZURE_SEARCH_CONTENT_FIELD", "content")
    
    for item in exported_data:
        # Extract the document text and metadata
        doc_content = item.get(content_field, "")
        if not doc_content:
            continue
            
        # Create LangChain document
        document = Document(
            page_content=doc_content,
            metadata=item
        )
        documents.append(document)
    
    # Add documents to vector store
    vector_store.add_documents(documents)
    print(f"Imported {len(documents)} documents into ChromaDB")

if __name__ == "__main__":
    import asyncio
    asyncio.run(import_to_chroma())
```

## Additional Considerations

### Deployment Options

For deploying the Python FastAPI backend:

1. **Docker Containerization**
   ```bash
   # Example Dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Cloud Deployment Options**
   - **Azure App Service**: Deploy as a containerized application
   - **AWS Lambda with API Gateway**: For serverless deployment
   - **Google Cloud Run**: For containerized applications
   - **Digital Ocean App Platform**: Simple deployment from GitHub

3. **Self-hosted Options**
   - **Gunicorn + Uvicorn**: For production-grade deployments
   - **Nginx as a reverse proxy**: For SSL termination and load balancing

### Performance Considerations

- **Separate Vector Database Service**: For production, consider running ChromaDB as a separate service
- **Connection Pooling**: Implement connection pooling for database connections
- **Caching**: Add caching for frequently accessed data
- **Horizontal Scaling**: Use multiple instances behind a load balancer for higher loads

### Monitoring and Logging

Add proper monitoring and logging to track:
- API request/response times
- Error rates
- Token usage with OpenAI
- Vector database performance metrics

## Conclusion

This guide provides a comprehensive approach to rewriting the TypeScript backend to Python with FastAPI, LangChain, and a vector database. The implementation leverages Python's ecosystem for AI applications while delivering the same functionality as the original TypeScript backend.

By following these steps, you'll create a maintainable and extensible Python backend that can be easily expanded with additional LangChain components and integrations, while taking advantage of direct OpenAI API access for the latest models and features.
