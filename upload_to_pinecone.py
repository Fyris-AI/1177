# upload_to_pinecone.py
import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
import time
import hashlib # For creating deterministic IDs

# --- Configuration ---
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT") # Needed for PodSpec, less so for ServerlessSpec client init
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Ensure this is set in your .env file

# --- Pinecone Index Details ---
PINECONE_INDEX_NAME = "medical-rag-index" # <<< Choose your Pinecone index name
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSION = 1536 # Dimension for text-embedding-3-small
UPSERT_BATCH_SIZE = 100 # Pinecone recommends batching upserts

# --- Paths ---
# Use the directory with the cleaned documents
CLEANED_DOCUMENTS_PATH = "/Users/buyn/Desktop/poc-1177/web_scraping/cleaned_markdown_documents"

# --- Splitting Threshold ---
# Documents with character count below or equal to this will NOT be split.
# 100 lines is usually very short for embedding context. ~1500 chars might be a better starting point.
# Adjust this based on your embedding model and desired chunk size.
NO_SPLIT_THRESHOLD_CHARS = 1500

# --- Headers for Splitting (if MarkdownHeaderTextSplitter is used) ---
HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"), # Add more if needed
]

def generate_deterministic_id(text: str) -> str:
    """Generates a SHA-256 hash as a deterministic ID for a text chunk."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load_and_process_documents(path: str) -> list:
    """Loads documents, conditionally splits them, keeping page_content and source."""
    print(f"Loading documents from: {path}")
    # Check if directory exists
    if not os.path.isdir(path):
        print(f"Error: Directory not found - {path}")
        return []
        
    loader = DirectoryLoader(
        path,
        glob="*.md", # Only load markdown files
        loader_cls=UnstructuredMarkdownLoader,
        show_progress=True,
        use_multithreading=True,
        # loader_kwargs={'mode': 'elements'} # Could use 'elements' mode for finer control if needed
    )
    try:
        loaded_docs = loader.load()
    except Exception as e:
        print(f"Error loading documents: {e}")
        return []
        
    print(f"Loaded {len(loaded_docs)} documents.")
    if not loaded_docs:
        print("No documents were loaded. Check the directory path and file permissions.")
        return []

    final_docs = [] # Will store tuples: (id, text_content, metadata)
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False # Keep headers in content for context
    )
    # Alternative: RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    print(f"Processing documents (splitting if > {NO_SPLIT_THRESHOLD_CHARS} chars)...")
    processed_count = 0
    skipped_count = 0
    split_count = 0
    not_split_count = 0

    for doc in loaded_docs:
        if not hasattr(doc, 'page_content') or not doc.page_content or not doc.page_content.strip():
            skipped_count += 1
            continue

        doc_len = len(doc.page_content)
        source = doc.metadata.get('source', 'Unknown')
        source_metadata = {"source": source} # Minimal metadata

        if doc_len <= NO_SPLIT_THRESHOLD_CHARS:
            text = doc.page_content
            doc_id = generate_deterministic_id(f"{source}-{text}")
            final_docs.append((doc_id, text, source_metadata))
            not_split_count += 1
        else:
            # Document is larger, split it.
            try:
                chunks = splitter.split_text(doc.page_content)
                if not chunks:
                     print(f"Warning: Splitting produced no chunks for {source}. Skipping.")
                     skipped_count += 1
                     continue

                for i, chunk in enumerate(chunks):
                    chunk_text = chunk.page_content
                    if not chunk_text or not chunk_text.strip(): continue # Skip empty chunks
                    chunk_id = generate_deterministic_id(f"{source}-chunk{i}-{chunk_text}")
                    final_docs.append((chunk_id, chunk_text, source_metadata.copy()))
                split_count += 1
            except Exception as e:
                 print(f"Error splitting document {source}: {e}. Skipping.")
                 skipped_count +=1

        processed_count += 1
        if processed_count % 50 == 0:
             print(f"Processed {processed_count}/{len(loaded_docs)} documents...")


    print("-" * 20)
    print(f"Processing Summary:")
    print(f"  Total Loaded: {len(loaded_docs)}")
    print(f"  Skipped (Empty/Error): {skipped_count}")
    print(f"  Processed Docs/Chunks: {len(final_docs)}")
    print(f"    - From {split_count} split documents")
    print(f"    - From {not_split_count} non-split documents")
    print("-" * 20)

    if not final_docs:
        print("Error: No documents processed successfully. Exiting.")
        exit()

    return final_docs


def main():
    # 1. Load and Process Documents
    docs_data = load_and_process_documents(CLEANED_DOCUMENTS_PATH)
    if not docs_data: # Exit if loading/processing failed
        print("Exiting due to issues in document loading/processing.")
        return

    # 2. Initialize Embeddings
    print(f"Initializing embeddings using model: {EMBEDDING_MODEL}")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please ensure it is set correctly in your .env file.")
        return
    try:
        embeddings_client = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY, chunk_size=500) # Use smaller chunk for embedding API
    except Exception as e:
        print(f"Error initializing OpenAI embeddings: {e}")
        return

    # 3. Initialize Pinecone
    print("Initializing Pinecone connection...")
    if not PINECONE_API_KEY:
        print("Error: PINECONE_API_KEY not found in environment variables.")
        print("Please ensure it is set correctly in your .env file.")
        return
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
    except Exception as e:
        print(f"Error initializing Pinecone client: {e}")
        return

    # 4. Create or Connect to Pinecone Index
    # Get the list of existing index names correctly
    try:
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    except Exception as e:
        print(f"Error listing Pinecone indexes: {e}")
        return

    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating index '{PINECONE_INDEX_NAME}'...")
        try:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=VECTOR_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws', # Or 'gcp', 'azure'
                    region='us-east-1' # <<< Choose your desired region
                )
                # Or PodSpec:
                # spec=PodSpec(environment=PINECONE_ENVIRONMENT, pod_type="p1.x1")
            )
            print("Index creation request sent. Waiting for index to initialize (this may take a minute)...")
            # Add a check to wait until index is ready
            while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
                 print(".", end="", flush=True)
                 time.sleep(5)
            print("\nIndex ready.")
        except Exception as e:
            print(f"Error creating Pinecone index: {e}")
            # Consider attempting deletion if creation failed mid-way, or manual cleanup needed
            return
    else:
        print(f"Index '{PINECONE_INDEX_NAME}' already exists. Connecting...")

    try:
        index = pc.Index(PINECONE_INDEX_NAME)
        print("Index description:")
        print(index.describe_index_stats())
    except Exception as e:
        print(f"Error connecting to Pinecone index '{PINECONE_INDEX_NAME}': {e}")
        return

    # 5. Generate Embeddings and Upsert Manually in Batches
    print(f"Generating embeddings and upserting {len(docs_data)} documents/chunks...")
    upsert_count = 0
    for i in range(0, len(docs_data), UPSERT_BATCH_SIZE):
        batch = docs_data[i : i + UPSERT_BATCH_SIZE]
        ids_batch = [item[0] for item in batch]
        texts_batch = [item[1] for item in batch]
        metadata_batch = [item[2] for item in batch] # Minimal metadata

        print(f"  Processing batch {i // UPSERT_BATCH_SIZE + 1}... Embedding {len(texts_batch)} texts...")
        try:
            embeds = embeddings_client.embed_documents(texts_batch)
        except Exception as e:
            print(f"    Error generating embeddings for batch: {e}")
            continue # Skip this batch

        # Prepare vectors for Pinecone upsert
        vectors_to_upsert = []
        if len(ids_batch) == len(embeds):
            for idx, embedding in enumerate(embeds):
                vectors_to_upsert.append({
                    "id": ids_batch[idx],
                    "values": embedding,
                    "metadata": metadata_batch[idx]
                    # Note: We are NOT including the text here
                })
        else:
            print(f"    Error: Mismatch between number of IDs ({len(ids_batch)}) and embeddings ({len(embeds)}) in batch. Skipping upsert.")
            continue

        print(f"    Upserting {len(vectors_to_upsert)} vectors...")
        try:
            upsert_response = index.upsert(vectors=vectors_to_upsert) # namespace can be added here if needed
            upsert_count += upsert_response.upserted_count
            print(f"    Batch upserted. Total count: {upsert_count}")
        except Exception as e:
            print(f"    Error upserting batch to Pinecone: {e}")
            # Consider adding retry logic here

    print("-" * 20)
    print(f"Upsert finished. Total vectors upserted: {upsert_count}")
    print("Final index description:")
    try:
        print(index.describe_index_stats())
    except Exception as e:
        print(f"Could not get final index stats: {e}")
    print("Process finished.")


if __name__ == "__main__":
    main() 