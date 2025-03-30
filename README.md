# Fråga 1177

A project made by Fyris AI.

## Project Overview

This project uses a Python FastAPI backend with LangChain and ChromaDB for knowledge retrieval and OpenAI for natural language processing. The frontend is built with Next.js.

## Getting Started

To get the project up and running, follow these steps:

### Frontend Setup

1. Install frontend dependencies:

   ```bash
   npm install
   ```

2. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

3. Update your frontend `.env` file to point to the Python backend:

   ```
   FASTAPI_BACKEND_URL=http://localhost:8000
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Set up a Python virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

5. Update your backend `.env` file with your OpenAI API key:

   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4-turbo-preview
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small

   # ChromaDB configuration
   VECTOR_DB_PATH=./vector_db
   ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Loading and Embedding Data into ChromaDB

The system comes with a script to easily load documents from various formats, chunk them into appropriate sizes, and embed them into ChromaDB for retrieval.

### Supported Document Types

- Text files (.txt)
- PDF files (.pdf)
- CSV files (.csv)
- JSON files (.json)
- Markdown files (.md, .markdown)
- Directories containing any of the above

### Running the Data Loading Script

1. Make sure your OpenAI API key is set in the `.env` file
2. To load a single file:

   ```bash
   cd backend
   python scripts/load_data_to_chroma.py --file_path path/to/your/document.pdf
   ```

3. To load a directory of documents:

   ```bash
   python scripts/load_data_to_chroma.py --file_path path/to/your/documents/
   ```

4. Customize chunking parameters if needed:

   ```bash
   python scripts/load_data_to_chroma.py --file_path path/to/your/document.pdf --chunk_size 1500 --chunk_overlap 150
   ```

5. Specify a custom ChromaDB location:

   ```bash
   python scripts/load_data_to_chroma.py --file_path path/to/your/document.pdf --db_path ./my_custom_db
   ```

### Chunking and Embedding Process

The script performs the following steps:

1. **Loading**: Reads the document(s) from the specified path
2. **Chunking**: Splits the documents into smaller chunks for better embedding and retrieval
   - Default chunk size: 1000 characters
   - Default overlap: 200 characters (helps maintain context between chunks)
3. **Embedding**: Processes each chunk with OpenAI's embedding model
4. **Storage**: Stores the embedded chunks in ChromaDB for fast vector similarity search

### Best Practices for Chunking Documents

- **Chunk Size**: 
  - For general text: 1000-1500 characters works well
  - For technical content: Consider smaller chunks (500-1000 characters)
  - For narrative content: Larger chunks (1500-2000 characters) may preserve context better
- **Chunk Overlap**:
  - Usually 10-20% of the chunk size
  - Higher overlap preserves more context between chunks but increases storage requirements

## Accessing the Application

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

- `/` - Next.js frontend
- `/backend` - Python FastAPI backend
  - `/app` - Main backend code
  - `/scripts` - Utility scripts including the data loading script
