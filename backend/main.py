import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# --- Configuration & Initialization ---

# Load environment variables from .env file
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
PINECONE_TOP_K = int(os.getenv("PINECONE_TOP_K", 3)) # Default to 3 if not set

# Basic validation
if not all([PINECONE_API_KEY, PINECONE_INDEX_NAME, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, OPENAI_MODEL]):
    raise EnvironmentError("Missing required environment variables (Pinecone API Key/Index Name, OpenAI API Key/Models).")

# Initialize Pinecone client
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    # Optional: Check if index exists and is ready
    # if PINECONE_INDEX_NAME not in pc.list_indexes().names:
    #     raise ValueError(f"Pinecone index '{PINECONE_INDEX_NAME}' not found.")
    # index_description = pc.describe_index(PINECONE_INDEX_NAME)
    # if not index_description.status['ready']:
    #      raise ConnectionError(f"Pinecone index '{PINECONE_INDEX_NAME}' is not ready.")
    print(f"Successfully connected to Pinecone index '{PINECONE_INDEX_NAME}'.")
    print(index.describe_index_stats())
except Exception as e:
    raise ConnectionError(f"Failed to initialize Pinecone: {e}") from e

# Initialize OpenAI client
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("Successfully initialized OpenAI client.")
except Exception as e:
    raise ConnectionError(f"Failed to initialize OpenAI client: {e}") from e


# --- FastAPI App ---

app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing)
# Adjust origins as needed for your frontend setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] , # Allows all origins for simplicity, restrict in production!
    allow_credentials=True,
    allow_methods=["*"] , # Allows all methods
    allow_headers=["*"] , # Allows all headers
)

# --- Request/Response Models ---

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str] # List of source documents used
    context: list[str] # Add the context chunks here

# --- NEW Models for Context Formatting ---
class FormatContextRequest(BaseModel):
    question: str
    answer: str
    context: list[str]

class FormatContextResponse(BaseModel):
    formattedContext: str
# --- END NEW Models ---

# --- Helper Functions ---

def get_embedding(text: str, model: str):
    """Generates embedding for the given text using OpenAI."""
    try:
        response = openai_client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate text embedding.") from e

def generate_answer(query: str, context_chunks: list[str]):
    """Generates an answer using OpenAI based on the query and context."""
    system_prompt = """You are a helpful assistant providing information based ONLY on the provided context. Follow these instructions carefully:

**Instructions:**
1. Answer the user's query using only the information present in the 'Context' section below.
2. If the answer is not found in the context, clearly state that you cannot answer based on the provided information.

**Formatting Guidelines for Chat Readability:**
- Use standard Markdown for formatting.
- Use paragraphs for distinct ideas. Avoid excessive newlines. Ensure proper spacing between paragraphs.
- Use bullet points (starting with `- ` or `* ` followed by a space) for lists. Ensure list items are clearly formatted on separate lines.
- Use bold text (`**text**`) for emphasis where appropriate (e.g., headings or key terms if suitable).
- Keep the language clear and concise for a chat interface.
"""
    
    context_string = "\n\n---\n\n".join(context_chunks)
    
    user_prompt = f"Context:\n{context_string}\n\nQuery: {query}\n\nAnswer:"

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2, # Adjust temperature for creativity vs. factuality
            max_tokens=4096, # Adjust as needed
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer with OpenAI: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer.") from e

# --- NEW Helper for Context Formatting ---
async def format_and_highlight_context(question: str, answer: str, context_chunks: list[str]):
    """Formats context and highlights relevant parts using OpenAI."""
    system_prompt = """You are an expert text formatter. Your task is to take a user's question, the assistant's answer, and the raw context chunks used to generate that answer. 
First, combine the context chunks into a single, readable Markdown block. Maintain the structure and content of the original chunks, perhaps separating them with a horizontal rule (`---`) if appropriate.
Second, within that *complete* context block, identify and **bold** (using Markdown's `**...**`) the specific sentences or phrases that are most directly relevant to the provided answer for the given question. 
Return the *entire*, formatted Markdown block with the relevant parts bolded. Do NOT return only the bolded parts.

**Input:**
- User Question
- Assistant Answer
- Raw Context Chunks (list of strings)

**Output:**
- A single Markdown string containing the *entire* combined, formatted context, with relevant parts **bolded**.

**Example:**
Context Chunk 1: "The sky is blue due to Rayleigh scattering."
Context Chunk 2: "Sunlight reaches Earth's atmosphere and is scattered in all directions."
Question: "Why is the sky blue?"
Answer: "The sky appears blue because of Rayleigh scattering..."

Output:
"The sky is **blue due to Rayleigh scattering**.

---

Sunlight reaches Earth's atmosphere and is scattered in all directions."

**Formatting Guidelines:**
- Combine the context chunks logically.
- Use standard Markdown.
- Only bold the directly relevant text within the full context.
"""

    context_string = "\n\n---\n\n".join(context_chunks)

    user_prompt = f"User Question:\n{question}\n\nAssistant Answer:\n{answer}\n\nRaw Context:\n{context_string}\n\nFormatted and Highlighted Context:"

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL, # Or choose another model if preferred for this task
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1, # Lower temperature for more deterministic formatting
            max_tokens=2048, # Adjust based on expected context size
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error formatting context with OpenAI: {e}")
        # Consider how to handle this - maybe return raw context or a specific error message?
        # For now, raise an exception that the endpoint handler will catch.
        raise HTTPException(status_code=500, detail="Failed to format context.") from e
# --- END NEW Helper ---

# --- API Endpoints ---

@app.post("/query", response_model=QueryResponse)
async def query_index(request: QueryRequest):
    """Receives a query, finds relevant documents, generates an answer."""
    try:
        print(f"Received query: {request.query}")

        # 1. Get query embedding
        print(f"Generating embedding for query using {OPENAI_EMBEDDING_MODEL}...")
        query_embedding = get_embedding(request.query, OPENAI_EMBEDDING_MODEL)
        print(f"Embedding generated (dimension: {len(query_embedding)}).")

        # 2. Query Pinecone
        print(f"Querying Pinecone index '{PINECONE_INDEX_NAME}' with top_k={PINECONE_TOP_K}...")
        query_results = index.query(
            vector=query_embedding,
            top_k=PINECONE_TOP_K,
            include_metadata=True # Crucial to get the 'text' or 'source'
        )
        print(f"Received {len(query_results.get('matches', []))} results from Pinecone.")

        # 3. Extract context and sources
        context_chunks = []
        sources = set() # Use a set to avoid duplicate source names
        
        if query_results.get('matches'):
             # Try to extract text directly if stored in metadata (BEST PRACTICE)
             try:
                 # --- IMPORTANT: Adapt this based on how text was stored ---
                 # Check upload_to_pinecone.py or your Pinecone index structure.
                 # Common metadata keys might be 'text', 'chunk', 'page_content', etc.
                 # If text isn't in metadata, this won't work.
                 context_chunks = [match['metadata']['text'] for match in query_results['matches'] if 'text' in match.get('metadata', {})]
                 if not context_chunks:
                      print("Warning: Could not find 'text' field in Pinecone metadata. Context might be missing.")
                      # Fallback or alternative strategy needed if text isn't in metadata
                      # For now, we'll proceed without explicit context chunks if 'text' is missing.

                 # Extract source information (assuming 'source' is in metadata)
                 for match in query_results['matches']:
                     if 'source' in match.get('metadata', {}):
                         sources.add(match['metadata']['source'])

             except KeyError as e:
                 print(f"KeyError accessing metadata: {e}. Ensure 'text' and 'source' keys exist in your Pinecone metadata.")
                 # Handle the case where metadata structure is different or keys are missing
                 # Perhaps log the metadata structure of the first match for debugging:
                 # if query_results['matches']: print(f"Debug - First match metadata: {query_results['matches'][0].get('metadata')}")
                 pass # Continue even if metadata extraction fails partially

        else:
            print("No relevant documents found in Pinecone.")
            # Decide how to handle this - return a specific message or let the LLM handle it.
            # return QueryResponse(answer="No relevant information found in the knowledge base.", sources=[])

        # --- ADD LOGGING FOR RETRIEVED CHUNKS ---
        print("--- Retrieved Pinecone Context Chunks ---")
        if context_chunks:
            for i, chunk in enumerate(context_chunks):
                print(f"Chunk {i+1}:\n{chunk}\n---")
        else:
            print("(No context chunks extracted)")
        print("--- End Retrieved Chunks ---")
        # --- END LOGGING --- 

        if not context_chunks:
             print("Warning: No context chunks extracted from Pinecone results. Answer generation might be poor.")
             # Optionally return early:
             # return QueryResponse(answer="Could not retrieve relevant context to answer the query.", sources=[])


        print(f"Extracted {len(context_chunks)} context chunks.")
        print(f"Identified sources: {list(sources)}")

        # 4. Generate Answer using OpenAI
        print(f"Generating answer using {OPENAI_MODEL}...")
        answer = generate_answer(request.query, context_chunks)
        print("Answer generated.")

        return QueryResponse(answer=answer, sources=list(sources), context=context_chunks)

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except ConnectionError as conn_err:
        print(f"Connection Error: {conn_err}")
        raise HTTPException(status_code=503, detail=str(conn_err))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# --- NEW Endpoint for Context Formatting ---
@app.post("/api/format-context", response_model=FormatContextResponse)
async def format_context_endpoint(request: FormatContextRequest):
    """Receives question, answer, and context, returns formatted/highlighted context."""
    try:
        print(f"Received context formatting request for question: {request.question[:50]}..." )
        formatted_context = await format_and_highlight_context(
            request.question,
            request.answer,
            request.context
        )
        print("Context formatting successful.")
        return FormatContextResponse(formattedContext=formatted_context)
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions from the helper or validation
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred during context formatting: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal server error occurred during context formatting.")
# --- END NEW Endpoint ---

# --- Run Server (for local development) ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server...")
    # Allow reloading for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 