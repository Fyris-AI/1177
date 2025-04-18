import os
import json
import math
import re
from typing import List, Dict, Tuple, Set, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import ValidationError, BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatbotResponse

# Load environment variables from .env file in the current directory (backend/)
# Note: GOOGLE_APPLICATION_CREDENTIALS environment variable should be set for authentication
load_dotenv()

# --- Configuration ---
DATA_DIR = "data" # Relative path to the data directory FROM main.py's location (backend/)
BATCH_SIZE = 10   # Number of documents to process in each batch for LLM 1
DEBUG = True      # Set to True for verbose output

# --- API Key Handling & Model Setup ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Keep error message in English for developer clarity
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Make sure it's set in backend/.env")
genai.configure(api_key=api_key)

GEMINI_MODEL_NAME = "gemini-1.5-flash-latest" 

# Initialize the generative model clients (can be reused)
try:
    llm1_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    llm2_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
except Exception as e:
     raise RuntimeError(f"Failed to initialize Gemini model '{GEMINI_MODEL_NAME}': {e}")


# --- FastAPI App Initialization ---
app = FastAPI() # <<< DEFINE THE APP OBJECT HERE

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

def get_document_filenames(data_dir: str) -> List[str]:
    """Gets a list of .md filenames from the specified directory."""
    script_dir = os.path.dirname(__file__)
    full_data_dir = os.path.join(script_dir, data_dir)
    if not os.path.isdir(full_data_dir):
        print(f"Error: Data directory not found at '{full_data_dir}'") # Log in English
        return []
    try:
        all_files = [f for f in os.listdir(full_data_dir) if os.path.isfile(os.path.join(full_data_dir, f))]
        md_files = sorted([f for f in all_files if f.endswith('.md')]) # Sort for consistent batching
        if DEBUG:
            print(f"Found {len(md_files)} markdown files in {full_data_dir}.")
        return md_files
    except Exception as e:
        print(f"Error listing files in {full_data_dir}: {e}") # Log in English
        return []

def read_file_content(filepath: str) -> str:
    """Reads the entire content of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Prepend filename to content - assuming this is desired preprocessing
            # If filenames are already in the files, this might duplicate them. Adjust if needed.
            # filename = os.path.basename(filepath)
            # return f"{filename}\n{f.read()}" 
            return f.read() # Assuming files already have filename prepended as per user's previous message
    except Exception as e:
        print(f"Error reading file {filepath}: {e}") # Log in English
        return "" # Return empty string on error

def format_llm1_batch_prompt(user_query: str, batch_content: List[Tuple[str, str]]) -> str:
    """Formats the prompt for the first LLM (relevance check) for a batch."""
    doc_separator = "\n\n---\n\n"
    formatted_docs = []
    for filename, content in batch_content:
        # Add clear separators including the filename
        formatted_docs.append(f"--- Start Document: {filename} ---\n{content}\n--- End Document: {filename} ---")

    docs_string = doc_separator.join(formatted_docs)

    # Keep prompt in Swedish
    prompt = f"""Användarfråga: "{user_query}"

Dokumentbunt:
{docs_string}

Du har fått en bunt med flera dokument (avgränsade med --- Start Document: [filnamn] --- och --- End Document: [filnamn] ---). Gå igenom varje dokument i bunten noggrant. Identifiera ALLA dokument vars innehåll är relevant för att besvara användarfrågan.
Returnera en lista med endast de exakta filnamnen för alla relevanta dokument du hittar i denna bunt. Separera filnamnen med kommatecken (t.ex. fil1.md,fil3.md,fil8.md).
Om inga dokument i bunten är relevanta, svara endast 'Inga'. Svara inte med någon förklarande text före eller efter listan med filnamn eller 'Inga'.

Relevanta filnamn:"""
    return prompt

def parse_llm1_response(response_text: str, batch_filenames: List[str]) -> List[str]:
    """Parses the comma-separated or newline-separated filename list from LLM 1's response text."""
    response_text = response_text.strip()
    if response_text.lower() == 'inga' or not response_text:
        return []

    # Replace newlines with commas, then split by comma
    processed_text = response_text.replace('\n', ',')
    potential_filenames = [fname.strip() for fname in processed_text.split(',') if fname.strip()] # Ensure no empty strings

    # Validate filenames against the batch list to prevent hallucinations
    valid_filenames = [fname for fname in potential_filenames if fname in batch_filenames]

    if DEBUG and len(potential_filenames) != len(valid_filenames):
        invalid_found = [fname for fname in potential_filenames if fname not in batch_filenames]
        print(f"Warning: LLM 1 parsing found potential filenames not in the current batch: {invalid_found}") # Log in English

    # Further clean up potential empty strings resulting from parsing (redundant due to list comprehension filter, but safe)
    valid_filenames = [fname for fname in valid_filenames if fname]

    return valid_filenames


def call_llm_1_relevance_batch(model: genai.GenerativeModel, prompt: str) -> str:
    """Calls the first LLM (Gemini) for relevance check and returns the raw text response."""
    if DEBUG:
        print("-" * 20 + " LLM 1 (Relevance Check) - START " + "-" * 20)
        # Print first/last 500 chars of prompt if too long
        if len(prompt) > 1000:
             print(f"Prompt preview:\n{prompt[:500]}...\n...{prompt[-500:]}")
        else:
            print(f"Prompt:\n{prompt}")

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if DEBUG:
            print(f"LLM 1 Raw Response: {response_text}")
            print("-" * 20 + " LLM 1 (Relevance Check) - END " + "-" * 20)
        return response_text
    except Exception as e:
        print(f"Error during LLM 1 call: {e}") # Log in English
        # Consider how to handle API errors (e.g., retry, return empty)
        if DEBUG:
             print("-" * 20 + " LLM 1 (Relevance Check) - FAILED " + "-" * 20)
        return "Inga" # Default to 'Inga' on error

def format_llm2_prompt(user_query: str, relevant_context: str) -> str:
    """
    Formats the prompt for the second LLM, instructing it to generate a JSON response.
    """
    # Keep prompt in Swedish
    prompt = f"""Du är en hjälpsam AI-assistent. Din uppgift är att svara på användarens fråga baserat *endast* på den tillhandahållna kontexten nedan. Kontexten består av ett eller flera dokument, åtskilda av '--- Dokument: [filnamn] ---'. Varje dokument innehåller ofta en titel och en URL-källa nära början.

Svara ALLTID med ett JSON-objekt, och inget annat. JSON-objektet ska ha följande struktur:
{{
  "message": "Ett tydligt och koncist svar på användarens fråga, endast baserat på informationen i kontexten.",
  "source_links": ["En lista med URL-källor (strängar) från de specifika dokument i kontexten som informationen i 'message' hämtades från."],
  "source_names": ["En lista med korta, beskrivande namn (strängar) för de specifika dokument i kontexten som informationen i 'message' hämtades från. Försök extrahera den mest relevanta delen av dokumentets titel (ofta före ' - ')."]
}}

Viktiga regler:
- Basera svaret ('message') *enbart* på den givna kontexten. Om svaret inte finns, ange det i 'message'. Hitta inte på information.
- Inkludera *endast* länkar och namn från de dokument som faktiskt användes för att formulera svaret i 'message'.
- Om inga dokument i kontexten var relevanta för att svara, eller om kontexten är tom, returnera:
  {{
    "message": "Jag kunde inte hitta relevant information i de tillhandahållna dokumenten för att svara på din fråga.",
    "source_links": [],
    "source_names": []
  }}
- Se till att outputen är ett giltigt JSON-objekt och inget annat (ingen extra text före eller efter).

Användarens Fråga: "{user_query}"

Tillhandahållen Kontext:
---
{relevant_context}
---

JSON Svar:
"""
    return prompt

def generate_answer(model: genai.GenerativeModel, user_query: str, relevant_filenames: List[str], data_dir: str) -> ChatbotResponse:
    """
    Reads content for relevant filenames, calls the second LLM (Gemini) to generate
    a JSON response containing the answer and sources, parses and validates it, 
    and returns a ChatbotResponse object.
    """
    # Path relative to main.py location
    script_dir = os.path.dirname(__file__)
    full_data_dir = os.path.join(script_dir, data_dir)

    # Handle case where LLM 1 found no relevant files
    if not relevant_filenames:
         return ChatbotResponse(
             message="Jag kunde inte hitta några relevanta dokument för att svara på din fråga.",
             source_links=[], 
             source_names=[]
        )

    print("\n--- Preparing Context for LLM 2 ---")
    final_context_parts = []

    for filename in relevant_filenames:
        filepath = os.path.join(full_data_dir, filename)
        content = read_file_content(filepath)
        if content:
            # Just append the content for the LLM context
            # Ensure title/link info is present within the content itself for LLM 2
            final_context_parts.append(f"--- Dokument: {filename} ---\n{content}") 
        else:
             print(f"Warning: Could not read relevant file {filename} for final context.") 

    # If no context could be built (e.g., all files failed to read)
    if not final_context_parts:
          return ChatbotResponse(
             message="Ett fel uppstod: Kunde inte läsa innehållet i de relevanta dokumenten.",
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

    llm_response_text = "" # Initialize to ensure it exists for error logging
    try:
        # Call LLM 2, expecting JSON in response.text
        response = model.generate_content(llm2_prompt)
        llm_response_text = response.text.strip()

        if DEBUG:
            print(f"LLM 2 Raw Response Text (Expecting JSON):\n{llm_response_text}")

        # Attempt to find JSON block (handling potential markdown backticks)
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", llm_response_text, re.DOTALL | re.IGNORECASE)
        if json_match:
             json_string = json_match.group(1)
             if DEBUG: print("Extracted JSON from markdown block.")
        elif llm_response_text.startswith("{") and llm_response_text.endswith("}"):
             json_string = llm_response_text
             if DEBUG: print("Assuming raw response is JSON.")
        else:
             raise ValidationError("Could not find valid JSON object in LLM 2 response.")


        # Parse and validate the JSON string using the Pydantic model
        response_data = ChatbotResponse.model_validate_json(json_string)
        
        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - SUCCESS " + "-" * 20)
        return response_data # Return the validated Pydantic object

    except (ValidationError, json.JSONDecodeError) as json_val_error:
        print(f"Error parsing/validating JSON from LLM 2: {json_val_error}") # Log in English
        print(f"LLM 2 Raw Response Text was:\n{llm_response_text}")
        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - PARSE/VALIDATE FAILED " + "-" * 20)
        # Return a standard error response object
        return ChatbotResponse(
            message="Jag är ledsen, ett internt fel uppstod när svaret skulle bearbetas.",
            source_links=[],
            source_names=[],
        )
        
    except Exception as e:
        print(f"Error during LLM 2 call or processing: {e}") # Log in English
        print(f"LLM 2 Raw Response Text was:\n{llm_response_text}") # Log response text if available
        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - GENERAL FAILED " + "-" * 20)
        # Return a standard error response object
        return ChatbotResponse(
            message="Jag är ledsen, ett oväntat fel inträffade när svaret genererades.",
            source_links=[],
            source_names=[],
        )


# --- Main Pipeline Function ---

def run_new_cag_pipeline(user_query: str) -> str:
    """
    Runs the new Context-Augmented Generation pipeline using batch processing.
    Returns a JSON string matching the frontend format.
    """
    print(f"\n--- Starting New CAG Pipeline for Query: '{user_query}' ---")

    # 1. List documents
    all_filenames = get_document_filenames(DATA_DIR)
    if not all_filenames:
        # Create the response object and return its JSON representation
        error_response = ChatbotResponse(
            message="Kunde inte hitta några dokument att bearbeta.", 
            source_links=[], 
            source_names=[]
        )
        return error_response.model_dump_json(indent=2) # Return JSON string

    total_files = len(all_filenames)
    print(f"Found {total_files} documents to process.") # Added log

    # 2. Process in batches with LLM 1
    aggregated_relevant_filenames: Set[str] = set()
    num_batches = math.ceil(total_files / BATCH_SIZE)
    script_dir = os.path.dirname(__file__)
    full_data_dir = os.path.join(script_dir, DATA_DIR)
    
    print(f"Processing documents in {num_batches} batches of up to {BATCH_SIZE} files each.") # Added log

    for i in range(num_batches):
        start_index = i * BATCH_SIZE
        end_index = min(start_index + BATCH_SIZE, total_files) # Use min to avoid index out of bounds
        batch_filenames = all_filenames[start_index:end_index]
        
        current_batch_num = i + 1
        print(f"\n>>> Starting Batch {current_batch_num}/{num_batches} ({len(batch_filenames)} files) <<<") # Added log

        # Read content for the current batch
        batch_content: List[Tuple[str, str]] = []
        # Log added within the loop for clarity on file reading start
        print(f"Reading content for batch {current_batch_num}...") 
        for filename in batch_filenames:
            filepath = os.path.join(full_data_dir, filename)
            content = read_file_content(filepath)
            if content: # Only include files that were read successfully
                 batch_content.append((filename, content))
            else:
                 print(f"Warning: Skipping file {filename} due to read error.") # Log in English

        if not batch_content:
             print(f"Warning: Skipping batch {current_batch_num} as no content could be read.") # Log in English
             continue

        print(f"Content read for batch {current_batch_num}. Sending to LLM 1...") # Added log

        # Format prompt and call LLM 1
        llm1_prompt = format_llm1_batch_prompt(user_query, batch_content)
        # Use the initialized model client
        llm1_response_text = call_llm_1_relevance_batch(llm1_model, llm1_prompt) 

        # Parse response and aggregate filenames
        # Pass the original batch_filenames list for validation within parse_llm1_response
        batch_actual_filenames = [fn for fn, _ in batch_content] # Filenames actually read
        relevant_in_batch = parse_llm1_response(llm1_response_text, batch_actual_filenames)
        if DEBUG:
            print(f"Relevant files identified by LLM 1 in batch {current_batch_num}: {relevant_in_batch}")
        aggregated_relevant_filenames.update(relevant_in_batch)

        # Log added after LLM 1 call and parsing
        print(f"<<< Finished Batch {current_batch_num}/{num_batches}. Found {len(relevant_in_batch)} relevant files in this batch. >>>") 
        if DEBUG and relevant_in_batch: # Only print filenames if DEBUG is on and files were found
            print(f"Relevant files in batch {current_batch_num}: {relevant_in_batch}")
            
    print(f"\n--- Aggregation Complete ---")
    # Clarified log
    print(f"Total relevant files identified by LLM 1 across all batches: {len(aggregated_relevant_filenames)}") 
    # Sort for consistent order before passing to LLM 2
    sorted_relevant_filenames = sorted(list(aggregated_relevant_filenames))
    if DEBUG:
        # Renamed log variable for clarity
        print(f"All relevant filenames (sorted): {sorted_relevant_filenames}") 


    # 3. Call LLM 2 with relevant filenames
    # Use the initialized model client and pass DATA_DIR relative path
    final_response_object: ChatbotResponse = generate_answer(llm2_model, user_query, sorted_relevant_filenames, DATA_DIR)

    print("\n--- New CAG Pipeline Complete ---")
    
    # Convert the Pydantic model to a JSON string for output
    return final_response_object.model_dump_json(indent=2) # <-- Added .model_dump_json()


# --- Request Body Model ---
class ChatRequest(BaseModel):
    query: str

# --- API Endpoint ---
@app.post("/api/chat") # Don't define response_model here if returning plain JSON string
async def chat_endpoint(chat_request: ChatRequest):
    """
    API endpoint to handle chat requests.
    Takes a user query, runs the pipeline, and returns the pipeline's JSON string.
    """
    user_query = chat_request.query
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    print(f"\n--- Received API Request for Query: '{user_query}' ---")
    
    try:
        # Run the pipeline function which returns a JSON string
        response_json_str = run_new_cag_pipeline(user_query)
        
        # Parse the JSON string back into a Python dict to return as JSON response
        response_data = json.loads(response_json_str) 
        
        print("\n--- API Request Processing Complete ---")
        # Return the data as a JSON response
        return JSONResponse(content=response_data)

    except Exception as e:
        print(f"Error processing API request in endpoint: {e}")
        # Log the traceback for detailed debugging if needed
        import traceback
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"Internal server error processing chat request.")


# Remove the old __main__ block if it exists
# if __name__ == "__main__":
#     ...