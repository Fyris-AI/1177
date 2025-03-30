import os
import argparse
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    DirectoryLoader,
    PyPDFLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredMarkdownLoader
)
from dotenv import load_dotenv

load_dotenv()

def load_documents(file_path: str) -> List[Document]:
    """
    Load documents from a file path. Supports txt, pdf, csv, json, md files
    or directories containing these file types.
    """
    if os.path.isdir(file_path):
        # Handle directory loading
        loaders = []
        
        # Text files
        if any(f.endswith('.txt') for f in os.listdir(file_path)):
            loaders.append(DirectoryLoader(file_path, glob="**/*.txt", loader_cls=TextLoader))
        
        # PDF files
        if any(f.endswith('.pdf') for f in os.listdir(file_path)):
            loaders.append(DirectoryLoader(file_path, glob="**/*.pdf", loader_cls=PyPDFLoader))
        
        # CSV files
        if any(f.endswith('.csv') for f in os.listdir(file_path)):
            loaders.append(DirectoryLoader(file_path, glob="**/*.csv", loader_cls=CSVLoader))
            
        # Markdown files
        if any(f.endswith(('.md', '.markdown')) for f in os.listdir(file_path)):
            loaders.append(DirectoryLoader(file_path, glob="**/*.md", loader_cls=UnstructuredMarkdownLoader))
            loaders.append(DirectoryLoader(file_path, glob="**/*.markdown", loader_cls=UnstructuredMarkdownLoader))
        
        documents = []
        for loader in loaders:
            documents.extend(loader.load())
        
        return documents
    else:
        # Handle single file loading
        if file_path.endswith('.txt'):
            loader = TextLoader(file_path)
        elif file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.csv'):
            loader = CSVLoader(file_path)
        elif file_path.endswith('.json'):
            loader = JSONLoader(
                file_path=file_path,
                jq_schema='.[]',
                text_content=False
            )
        elif file_path.endswith(('.md', '.markdown')):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        return loader.load()

def chunk_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    Split documents into chunks for better embedding and retrieval.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    return text_splitter.split_documents(documents)

def embed_and_store(documents: List[Document], persist_directory: str):
    """
    Embed documents and store them in ChromaDB.
    """
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    embeddings = OpenAIEmbeddings(
        openai_api_key=api_key,
        model=embedding_model
    )
    
    # Initialize or get existing ChromaDB
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Add documents to ChromaDB
    db.add_documents(documents)
    
    print(f"Successfully embedded and stored {len(documents)} document chunks in ChromaDB at {persist_directory}")
    return db

def main():
    parser = argparse.ArgumentParser(description="Load and embed documents into ChromaDB")
    parser.add_argument("--file_path", required=True, help="Path to document file or directory")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Size of document chunks")
    parser.add_argument("--chunk_overlap", type=int, default=200, help="Overlap between chunks")
    parser.add_argument("--db_path", default="./vector_db", help="Path to store the ChromaDB")
    
    args = parser.parse_args()
    
    print(f"Loading documents from {args.file_path}...")
    documents = load_documents(args.file_path)
    print(f"Loaded {len(documents)} documents")
    
    print(f"Chunking documents with chunk size {args.chunk_size} and overlap {args.chunk_overlap}...")
    chunked_documents = chunk_documents(documents, args.chunk_size, args.chunk_overlap)
    print(f"Created {len(chunked_documents)} chunks")
    
    print("Embedding and storing chunks in ChromaDB...")
    db = embed_and_store(chunked_documents, args.db_path)
    print("Completed!")

if __name__ == "__main__":
    main() 