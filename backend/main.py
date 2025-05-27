import os
import json
import math
import re
import concurrent.futures
from typing import List, Dict, Tuple, Set, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import ValidationError, BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from models import ChatbotResponse

# Load environment variables from .env file in the current directory (backend/)
# Note: GOOGLE_APPLICATION_CREDENTIALS environment variable should be set for authentication
load_dotenv()

# --- Configuration ---
DATA_DIR = "data/markdown"  # Base data directory
BATCH_SIZE = 5  # Number of documents to process in each batch for LLM 1
DEBUG = True  # Set to True for verbose output
MAX_WORKERS = 20  # Max concurrent workers for LLM 1 batches (Added)

# --- API Key Handling & Model Setup ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Keep error message in English for developer clarity
    raise ValueError(
        "GOOGLE_API_KEY not found in environment variables. Make sure it's set in backend/.env"
    )
genai.configure(api_key=api_key)

GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

# Initialize the generative model clients (can be reused)
try:
    llm1_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    llm2_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
except Exception as e:
    raise RuntimeError(
        f"Failed to initialize Gemini model '{GEMINI_MODEL_NAME}': {e}")

# --- FastAPI App Initialization ---
app = FastAPI()  # <<< DEFINE THE APP OBJECT HERE

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---


def get_document_filenames(base_data_dir: str) -> List[str]:
    """Gets a list of .md filenames from the data directory."""
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, base_data_dir)
    print(f"LOG: [get_document_filenames] Attempting to list files in: {data_dir}")

    is_dir = os.path.isdir(data_dir)
    print(f"LOG: [get_document_filenames] Is directory? ({data_dir}): {is_dir}")
    if not is_dir:
        print(f"Error: Data directory not found or not a directory at '{data_dir}'")
        return []

    try:
        all_files = [
            f for f in os.listdir(data_dir)
            if os.path.isfile(os.path.join(data_dir, f))
        ]
        print(f"LOG: [get_document_filenames] Found {len(all_files)} files/items before filtering: {all_files[:10]}...")
        md_files = sorted([f for f in all_files if f.endswith('.md')])
        print(f"LOG: [get_document_filenames] Found {len(md_files)} markdown files in {data_dir}.")
        return md_files
    except Exception as e:
        print(f"Error listing files in {data_dir}: {e}")
        return []


def read_file_content(filepath: str) -> str:
    """Reads the entire content of a file."""
    # ADDED LOG
    print(f"LOG: [read_file_content] Attempting to read file: {filepath}")
    if not os.path.isfile(filepath):
        print(f"Error: [read_file_content] File not found at path: {filepath}")
        return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return ""


def format_llm1_batch_prompt(user_query: str,
                             batch_content: List[Tuple[str, str]]) -> str:
    """Formats the prompt for the first LLM (relevance check) for a batch."""
    doc_separator = "\n\n---\n\n"
    formatted_docs = []
    for filename, content in batch_content:
        # Add clear separators including the filename
        formatted_docs.append(
            f"--- Start Document: {filename} ---\n{content}\n--- End Document: {filename} ---"
        )

    docs_string = doc_separator.join(formatted_docs)

    prompt = f"""You are an AI assistant specialized in flap surgery, burn care, and related reconstructive surgery.\n\nUser question: \"{user_query}\"\n\nDocument batch:\n{docs_string}\n\nYou have received a batch of several documents (delimited by --- Start Document: [filename] --- and --- End Document: [filename] ---). Carefully review each document in the batch. Identify ALL documents whose content is relevant to answering the user's question.\nReturn a list containing ONLY the exact filenames of all relevant documents you find in this batch. Separate the filenames with commas (e.g. file1.md,file3.md,file8.md).\nIf none of the documents in the batch are relevant, reply only with 'None'. Do not include any explanatory text before or after the list of filenames or 'None'.\n\nRelevant filenames:"""
    return prompt


def parse_llm1_response(response_text: str,
                        batch_filenames: List[str]) -> List[str]:
    """Parses the comma-separated or newline-separated filename list from LLM 1's response text."""
    response_text = response_text.strip()
    print(f"LOG: [parse_llm1_response] Raw response to parse: '{response_text}'") # ADDED LOG
    if response_text.lower() == 'inga' or not response_text:
        print("LOG: [parse_llm1_response] Parsed as no relevant files ('Inga' or empty).") # ADDED LOG
        return []

    # Replace newlines with commas, then split by comma
    processed_text = response_text.replace('\\n', ',')
    potential_filenames = [
        fname.strip() for fname in processed_text.split(',') if fname.strip()
    ]

    print(f"LOG: [parse_llm1_response] Potential filenames after split: {potential_filenames}") # ADDED LOG

    # Validate filenames against the batch list to prevent hallucinations
    valid_filenames = [
        fname for fname in potential_filenames if fname in batch_filenames
    ]

    if len(potential_filenames) != len(valid_filenames):
        invalid_found = [
            fname for fname in potential_filenames
            if fname not in batch_filenames
        ]
        # Log in English
        print(
            f"Warning: LLM 1 parsing found potential filenames not in the current batch: {invalid_found}"
        )

    # Further clean up potential empty strings resulting from parsing
    valid_filenames = [fname for fname in valid_filenames if fname]
    print(f"LOG: [parse_llm1_response] Validated filenames: {valid_filenames}") # ADDED LOG

    return valid_filenames


def call_llm_1_relevance_batch(model: genai.GenerativeModel,
                               prompt: str) -> str:
    """Calls the first LLM (Gemini) for relevance check and returns the raw text response."""
    if DEBUG:
        print("-" * 20 + " LLM 1 (Relevance Check) - START " + "-" * 20)
        if len(prompt) > 1000:
            print(f"Prompt preview:\\n{prompt[:500]}...\\n...{prompt[-500:]}")
        else:
            print(f"Prompt:\\n{prompt}")

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if DEBUG:
            print(f"LLM 1 Raw Response: {response_text}")
            print("-" * 20 + " LLM 1 (Relevance Check) - END " + "-" * 20)
        return response_text
    except Exception as e:
        print(f"Error during LLM 1 call: {e}")
        if DEBUG:
            print("-" * 20 + " LLM 1 (Relevance Check) - FAILED " + "-" * 20)
        return "Inga"  # Default to 'Inga' on error


def format_llm2_prompt(user_query: str, relevant_context: str) -> str:
    """
    Formats the prompt for the second LLM, instructing it to generate a JSON response.
    """
    prompt = f"""You are an AI assistant specialized in flap surgery, burn care, and related reconstructive surgery. Your task is to answer the user's question based on the provided context below. The context consists of one or more documents, separated by '--- Document: [filename] ---'. Each document often contains a title and a source URL near the beginning.\n\nALWAYS respond with a JSON object, and nothing else. The JSON object should have the following structure:\n{{\n  \"message\": \"A clear and concise answer to the user's question based on the information in the context.\",\n  \"source_links\": [\"A list of URL sources (strings) from the specific documents in the context that the information in 'message' was taken from.\"],\n  \"source_names\": [\"A list of short, descriptive names (strings) for the specific documents in the context that the information in 'message' was taken from. Try to extract the most relevant part of the document's title (often before ' - ').\"]\n}}\n\nImportant rules:\n- Base the answer ('message') strictly on the given context. Do not make up information.\n- Include *only* links and names from the documents that were actually used to formulate the answer in 'message'.\n- If none of the documents in the context were relevant to answer, or if the context is empty, return:\n  {{\n    \"message\": \"I could not find relevant information in the provided documents to answer your question.\",\n    \"source_links\": [],\n    \"source_names\": []\n  }}\n- Ensure the output is a valid JSON object and nothing else (no extra text before or after).\n\nUser Question: \"{user_query}\"\n\nProvided Context:\n---\n{relevant_context}\n---\n\nJSON Answer:\n"""
    return prompt


def generate_answer(model: genai.GenerativeModel, user_query: str,
                    relevant_filenames: List[str],
                    base_data_dir: str) -> ChatbotResponse:
    """
    Reads content for relevant filenames, calls the second LLM,
    parses and validates JSON response, and returns a ChatbotResponse object.
    """
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, base_data_dir)
    print(f"LOG: [generate_answer] Using data directory: {data_dir}")

    if not relevant_filenames:
        print("LOG: [generate_answer] No relevant filenames provided by LLM 1.")
        # Check if the query is related to flap surgery
        if any(term in user_query.lower() for term in ['flap', 'flaps', 'reconstruction', 'surgery']):
            return ChatbotResponse(
                message="I could not find any specific documents about this particular flap surgery technique. However, I have information about various other flap surgeries and reconstructive procedures. Would you like to know about a different type of flap surgery?",
                source_links=[],
                source_names=[])
        else:
            return ChatbotResponse(
                message="I could not find any specific documents that directly answer your question. However, I have information about various medical conditions and procedures. Would you like to try asking about a different topic?",
                source_links=[],
                source_names=[])

    print("\n--- Preparing Context for LLM 2 ---")
    final_context_parts = []

    for filename in relevant_filenames:
        filepath = os.path.join(data_dir, filename)
        print(f"LOG: [generate_answer] Reading relevant file: {filepath}")
        content = read_file_content(filepath)
        if content:
            final_context_parts.append(f"--- Document: {filename} ---\n{content}")
        else:
            print(f"Warning: Could not read relevant file {filename} from {data_dir} for final context.")

    if not final_context_parts:
        print("Error: [generate_answer] Could not build final context (all relevant files failed to read).")
        return ChatbotResponse(
            message="An error occurred: Could not read the content of the relevant documents.",
            source_links=[],
            source_names=[],
        )

    final_context = "\n\n".join(final_context_parts)

    print("\n--- Calling LLM 2 for Final Answer JSON ---")
    llm2_prompt = format_llm2_prompt(user_query, final_context)

    if DEBUG:
        print("-" * 20 + " LLM 2 (JSON Generation) - START " + "-" * 20)
        if len(llm2_prompt) > 1000:
            print(f"Prompt preview:\n{llm2_prompt[:500]}...\n...{llm2_prompt[-500:]}")
        else:
            print(f"Prompt:\n{llm2_prompt}")

    llm_response_text = ""
    try:
        response = model.generate_content(llm2_prompt)
        llm_response_text = response.text.strip()

        if DEBUG:
            print(f"LLM 2 Raw Response Text (Expecting JSON):\n{llm_response_text}")

        # Attempt to find JSON block
        json_string = None
        json_match = re.search(r"```(?:json)?\\s*(\\{.*?\\})\\s*```",
                               llm_response_text, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_string = json_match.group(1)
            if DEBUG: print("LOG: Extracted JSON using regex from markdown block.")
        else:
            try:
                start_index = llm_response_text.index('{')
                end_index = llm_response_text.rindex('}')
                json_string = llm_response_text[start_index:end_index + 1]
                if DEBUG: print("LOG: Extracted JSON using first '{' and last '}'.")
            except ValueError:
                pass

        if json_string is None:
            print(f"Error: [generate_answer] Failed to extract JSON block from raw response. Raw response:\n{llm_response_text}")
            raise ValueError("Could not extract a potential JSON object from LLM 2 response.")

        if DEBUG:
            print(f"LOG: Attempting to parse JSON string:\n{json_string}")

        response_data = ChatbotResponse.model_validate_json(json_string)
        print("LOG: [generate_answer] Successfully parsed JSON from LLM 2.")

        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - SUCCESS " + "-" * 20)
        return response_data

    except (ValidationError, json.JSONDecodeError) as json_val_error:
        print(f"Error parsing/validating JSON from LLM 2: {json_val_error}")
        print(f"LLM 2 Raw Response Text was:\n{llm_response_text}")
        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - PARSE/VALIDATE FAILED " + "-" * 20)
        return ChatbotResponse(
            message="Sorry, an internal error occurred while processing the answer.",
            source_links=[],
            source_names=[],
        )

    except Exception as e:
        print(f"Error during LLM 2 call or processing: {e}")
        print(f"LLM 2 Raw Response Text was:\n{llm_response_text}")
        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - GENERAL FAILED " + "-" * 20)
        return ChatbotResponse(
            message="Sorry, an unexpected error occurred while generating the answer.",
            source_links=[],
            source_names=[],
        )


# --- Helper function for parallel batch processing ---
def process_single_batch(batch_filenames: List[str], user_query: str,
                         base_data_dir: str,
                         model: genai.GenerativeModel,
                         batch_num: int, total_batches: int) -> List[str]:
    """Processes a single batch: reads files, calls LLM 1, parses results."""
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, base_data_dir)
    print(f"LOG: [process_single_batch {batch_num}/{total_batches}] Using data directory: {data_dir}")
    print(f"\n>>> Starting Batch {batch_num}/{total_batches} ({len(batch_filenames)} files) [Threaded] <<<")

    batch_content: List[Tuple[str, str]] = []
    print(f"Reading content for batch {batch_num} from {data_dir}...")
    for filename in batch_filenames:
        filepath = os.path.join(data_dir, filename)
        content = read_file_content(filepath)
        if content:
            batch_content.append((filename, content))
        else:
            print(f"Warning: Skipping file {filename} in batch {batch_num} from {data_dir} due to read error.")

    if not batch_content:
        print(f"Warning: Skipping batch {batch_num} as no content could be read from {data_dir}.")
        return []

    print(f"Content read for batch {batch_num}. Sending to LLM 1...")

    llm1_prompt = format_llm1_batch_prompt(user_query, batch_content)
    llm1_response_text = call_llm_1_relevance_batch(model, llm1_prompt)

    batch_actual_filenames = [fn for fn, _ in batch_content]
    relevant_in_batch = parse_llm1_response(llm1_response_text, batch_actual_filenames)

    print(f"<<< Finished Batch {batch_num}/{total_batches}. Found {len(relevant_in_batch)} relevant files. [Threaded] >>>")
    if DEBUG and relevant_in_batch:
        print(f"Relevant files in batch {batch_num}: {relevant_in_batch}")

    return relevant_in_batch


# --- Main Pipeline Function ---


def run_new_cag_pipeline(user_query: str) -> str:
    """
    Runs the new CAG pipeline using parallel batch processing for the personal audience.
    Returns a JSON string matching the frontend format.
    """
    print(f"\n--- Starting New CAG Pipeline for Query: '{user_query}' ---")

    all_filenames = get_document_filenames(DATA_DIR)
    if not all_filenames:
        error_response = ChatbotResponse(
            message="I apologize, but I could not find any documents in my knowledge base. This might be due to a technical issue. Please try again later.",
            source_links=[],
            source_names=[])
        return error_response.model_dump_json(indent=2)

    total_files = len(all_filenames)
    print(f"Found {total_files} documents to process.")

    aggregated_relevant_filenames: Set[str] = set()
    num_batches = math.ceil(total_files / BATCH_SIZE)

    batches = []
    for i in range(num_batches):
        start_index = i * BATCH_SIZE
        end_index = min(start_index + BATCH_SIZE, total_files)
        batches.append(all_filenames[start_index:end_index])

    print(f"Processing documents in {num_batches} batches of up to {BATCH_SIZE} files each using up to {MAX_WORKERS} parallel workers.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch_num = {
            executor.submit(
                process_single_batch,
                batch_filenames,
                user_query,
                DATA_DIR,
                llm1_model,
                i + 1,
                num_batches):
            i + 1
            for i, batch_filenames in enumerate(batches)
        }

        for future in concurrent.futures.as_completed(future_to_batch_num):
            batch_num = future_to_batch_num[future]
            try:
                relevant_in_batch = future.result()
                aggregated_relevant_filenames.update(relevant_in_batch)
            except Exception as exc:
                print(f'Batch {batch_num} generated an exception: {exc}')

    print(f"\n--- Aggregation Complete ---")
    print(f"Total relevant files identified by LLM 1 across all batches: {len(aggregated_relevant_filenames)}")
    if DEBUG and aggregated_relevant_filenames:
        print(f"Aggregated relevant filenames: {sorted(list(aggregated_relevant_filenames))}")

    final_response_object: ChatbotResponse = generate_answer(
        llm2_model, user_query, sorted(list(aggregated_relevant_filenames)),
        DATA_DIR)

    print("\n--- New CAG Pipeline Complete ---")

    return final_response_object.model_dump_json(indent=2)


# --- Request Body Model ---
class ChatRequest(BaseModel):
    query: str


# --- API Endpoint ---
@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    """
    API endpoint to handle chat requests.
    Takes a user query, runs the pipeline, and returns the JSON string.
    """
    user_query = chat_request.query

    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    print(f"\n--- Received API Request --- Query: '{user_query}' ---")

    try:
        response_json_str = run_new_cag_pipeline(user_query)
        response_data = json.loads(response_json_str)
        print("\n--- API Request Processing Complete ---")
        return JSONResponse(content=response_data)

    except Exception as e:
        print(f"Error processing API request in endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error processing chat request.")
