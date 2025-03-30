# Python Backend with FastAPI, LangChain, and OpenAI

This is a Python backend implementation that replaces the original TypeScript backend, using FastAPI, LangChain, and direct OpenAI API integration.

## Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Clone the repository
2. Navigate to the backend directory:
   ```bash
   cd backend
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables by copying the sample `.env` file and filling in your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configurations
   ```

## Environment Variables

The following environment variables are used:

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: The OpenAI model to use (default: "gpt-4-turbo-preview")
- `OPENAI_EMBEDDING_MODEL`: The OpenAI embedding model to use (default: "text-embedding-3-small")
- `VECTOR_DB_TYPE`: The vector database to use (default: "chroma")
- `VECTOR_DB_PATH`: The path to store the vector database (default: "./vector_db")

## Running the Server

Start the server:

```bash
uvicorn app.main:app --reload
```

The server will be available at `http://localhost:8000`.

## API Endpoints

### Chat API

- **URL**: `/api/chat`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "What can you tell me about AI?"
      }
    ]
  }
  ```
- **Response**: Server-sent events stream

## Data Migration

If you're migrating from Azure AI Search, you can use the provided scripts:

1. Export data from Azure AI Search:
   ```bash
   python scripts/export_from_azure.py
   ```

2. Import data to ChromaDB:
   ```bash
   python scripts/import_to_chroma.py
   ```

## Project Structure

- `app/`: Main application code
  - `main.py`: FastAPI application entry point
  - `routes/`: API routes
    - `chat.py`: Chat API endpoint
  - `services/`: Service layer
    - `ai.py`: AI service for LangChain integration
    - `vector_store.py`: Vector database service
  - `utils/`: Utility functions
    - `config.py`: Configuration utilities
- `scripts/`: Utility scripts
  - `export_from_azure.py`: Script to export data from Azure AI Search
  - `import_to_chroma.py`: Script to import data to ChromaDB

## Frontend Integration

To update your frontend to work with this new API, update your API client to point to the new FastAPI endpoint. For example:

```typescript
// client-side update to point to the new backend
import { createChat } from 'ai';

const { messages, input, handleInputChange, handleSubmit, isLoading } = createChat({
  api: 'http://localhost:8000/api/chat', // Update with your FastAPI URL
  headers: {
    'Content-Type': 'application/json',
  },
});
``` 