import os
import json
import math
import re
import concurrent.futures
from typing import List, Dict, Tuple, Set, Optional, Any
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import ValidationError, BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from models import ChatbotResponse, ClarifyingOption

# Load environment variables from .env file in the current directory (backend/)
# Note: GOOGLE_APPLICATION_CREDENTIALS environment variable should be set for authentication
load_dotenv()

# --- Configuration ---
DATA_DIR = "data"  # Base data directory
BATCH_SIZE = 20  # Number of documents to process in each batch for LLM 1
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

GEMINI_MODEL_NAME = "gemini-2.0-flash"

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


def get_document_filenames(base_data_dir: str, audience: str) -> List[str]:
    """Gets a list of .md filenames from the audience-specific subdirectory."""
    script_dir = os.path.dirname(__file__)
    # Construct path: backend/data/{audience}
    audience_data_dir = os.path.join(script_dir, base_data_dir, audience)
    print(f"LOG: [get_document_filenames] Attempting to list files in: {audience_data_dir}") # ADDED LOG

    is_dir = os.path.isdir(audience_data_dir)
    print(f"LOG: [get_document_filenames] Is directory? ({audience_data_dir}): {is_dir}") # ADDED LOG
    if not is_dir:
        print(f"Error: Audience data directory not found or not a directory at '{audience_data_dir}'")
        return []

    try:
        all_files = [
            f for f in os.listdir(audience_data_dir)
            if os.path.isfile(os.path.join(audience_data_dir, f))
        ]
        print(f"LOG: [get_document_filenames] Found {len(all_files)} files/items before filtering: {all_files[:10]}...") # ADDED LOG
        md_files = sorted([f for f in all_files if f.endswith('.md')])
        print(f"LOG: [get_document_filenames] Found {len(md_files)} markdown files in {audience_data_dir}.") # UPDATED LOG
        return md_files
    except Exception as e:
        print(f"Error listing files in {audience_data_dir}: {e}")
        return []


def truncate_citation_name(name: str, max_length: int = 30) -> str:
    """
    Truncates a citation name to max_length characters, adding "..." if truncated.
    """
    if not name or not isinstance(name, str):
        return ""
    name = name.strip()
    if len(name) <= max_length:
        return name
    return name[:max_length - 3] + "..."


def extract_document_metadata(content: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts URL and Title metadata from document content.
    Returns (url, title) tuple. Returns (None, None) if not found.
    """
    url = None
    title = None
    
    lines = content.split('\n')
    for i, line in enumerate(lines[:10]):  # Check first 10 lines for metadata
        if line.startswith('URL Source:'):
            url = line.replace('URL Source:', '').strip()
        elif line.startswith('Title:'):
            title = line.replace('Title:', '').strip()
    
    return (url, title)


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
    doc_separator = "\\n\\n---\\n\\n"
    formatted_docs = []
    for filename, content in batch_content:
        # Add clear separators including the filename
        formatted_docs.append(
            f"--- Start Document: {filename} ---\\n{content}\\n--- End Document: {filename} ---"
        )

    docs_string = doc_separator.join(formatted_docs)

    # Keep prompt in Swedish
    prompt = f"""Användarfråga: "{user_query}"

Dokumentbunt:
{docs_string}

Du har fått en bunt med flera dokument (avgränsade med --- Start Document: [filnamn] --- och --- End Document: [filnamn] ---). 

MYCKET VIKTIGT - FRÅGOR OM PERSONLIG JOURNAL/SJUKHISTORIA:
Om användarfrågan handlar om användarens EGEN journal, sjukhistoria, labvärden, undersökningar eller medicinska historik (t.ex. "min journal", "min sjukhistoria", "mina labvärden", "sammanfatta min...", "vad säger journalen"), ska du svara 'Inga' eftersom dessa dokument från 1177.se INTE innehåller personlig patientdata.
Personliga journalfrågor kräver INTE offentliga 1177.se-dokument.

VIKTIGT: Var STRIKT vid bedömning av relevans. Ett dokument är ENDAST relevant om det:
1. Handlar om SAMMA ämne/sjukdom/tillstånd som användarfrågan
2. Kan ge DIREKT information för att besvara frågan
3. Frågan handlar om ALLMÄN medicinsk information (INTE om användarens personliga journal)

INKLUDERA INTE dokument som bara:
- Innehåller liknande ord (t.ex. "risk" i en fråga om demens matchar INTE "risk för hudcancer")
- Handlar om ett helt annat medicinskt område
- Bara tangentiellt nämner ämnet
- Är generell information när frågan handlar om användarens PERSONLIGA data

Identifiera ENDAST de dokument vars innehåll är DIREKT relevant för att besvara användarfrågan.
Returnera en lista med endast de exakta filnamnen för relevanta dokument. Separera filnamnen med kommatecken (t.ex. fil1.md,fil3.md).
Om inga dokument i bunten är relevanta, svara endast 'Inga'. Svara inte med någon förklarande text före eller efter listan med filnamn eller 'Inga'.

Relevanta filnamn:"""
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


def format_llm2_prompt(user_query: str, relevant_context: str, document_metadata: Dict[str, Dict[str, str]]) -> str:
    """
    Formats the prompt for the second LLM, instructing it to generate a JSON response.
    document_metadata: Dict mapping filename -> {"url": "...", "title": "..."}
    """
    # Build metadata reference section for the prompt
    metadata_section = ""
    if document_metadata:
        metadata_section = "\n\nViktig information om dokumentmetadata:\n"
        for filename, meta in document_metadata.items():
            if meta.get("url") or meta.get("title"):
                metadata_section += f"- Dokument '{filename}': "
                if meta.get("title"):
                    metadata_section += f"Titel: {meta['title']}, "
                if meta.get("url"):
                    metadata_section += f"URL: {meta['url']}"
                metadata_section += "\n"
    
    # Keep prompt in Swedish
    prompt = f"""Du är en hjälpsam AI-assistent. Din uppgift är att svara på användarens fråga baserat på den tillhandahållna kontexten nedan. Kontexten består av ett eller flera dokument, åtskilda av '--- Dokument: [filnamn] ---'. Varje dokument börjar med metadata-rader som innehåller "Filename:", "Title:", och "URL Source:" högst upp i dokumentet.

Svara ALLTID med ett JSON-objekt, och inget annat. JSON-objektet ska ha följande struktur:
{{
  "message": "Ett tydligt och koncist svar på användarens fråga baserat på informationen i kontexten.",
  "source_links": ["MAXIMALT 3-4 URL-källor från de MEST relevanta dokumenten. Hämta URL:en från 'URL Source:' i varje dokument."],
  "source_names": ["MAXIMALT 3-4 korta namn (max 30 tecken). Hämta från 'Title:' i varje dokument."]
}}

KRITISKA REGLER:
- MAXIMALT 3-4 källor - välj de MEST relevanta dokumenten för frågan, använd endast en källa om om den är direkt relevant till frågan
- Du MÅSTE ALLTID inkludera source_links och source_names när du refererar till information från 1177.se
- ALDRIG säg "Du kan läsa mer på 1177.se" utan att inkludera den specifika URL:en i source_links
- Om det finns relevanta dokument i kontexten, ANVÄND dem och INKLUDERA deras länkar
- Varje dokument i kontexten har metadata högst upp: leta efter rader som börjar med "Title:" och "URL Source:"
- Om du använder information från ett dokument, MÅSTE du inkludera dess URL och titel

Andra viktiga regler:
- Basera svaret ('message') baserat på den givna kontexten. Hitta inte på information.
- Om inga dokument i kontexten var relevanta för att svara, eller om kontexten är tom, returnera:
  {{
    "message": "Jag kunde inte hitta relevant information i de tillhandahållna dokumenten för att svara på din fråga.",
    "source_links": [],
    "source_names": []
  }}
- Se till att outputen är ett giltigt JSON-objekt och inget annat (ingen extra text före eller efter).
- source_links och source_names måste ha samma längd och motsvarande positioner.

{metadata_section}

Användarens Fråga: "{user_query}"

Tillhandahållen Kontext:
---
{relevant_context}
---

JSON Svar:
"""
    return prompt


def generate_answer(model: genai.GenerativeModel, user_query: str,
                    relevant_filenames: List[str],
                    base_data_dir: str, audience: str) -> ChatbotResponse: # Added audience
    """
    Reads content for relevant filenames (using audience), calls the second LLM,
    parses and validates JSON response, and returns a ChatbotResponse object.
    """
    # Path relative to main.py location
    script_dir = os.path.dirname(__file__)
    # Construct path: backend/data/{audience}
    audience_data_dir = os.path.join(script_dir, base_data_dir, audience)
    print(f"LOG: [generate_answer] Using audience data directory: {audience_data_dir}") # ADDED LOG

    if not relevant_filenames:
        print("LOG: [generate_answer] No relevant filenames provided by LLM 1.") # ADDED LOG
        return ChatbotResponse(
            message=
            "Jag kunde inte hitta några relevanta dokument för att svara på din fråga.",
            source_links=[],
            source_names=[])

    print("\\n--- Preparing Context for LLM 2 ---")
    final_context_parts = []
    document_metadata = {}  # Store metadata for each document: filename -> {url, title}

    for filename in relevant_filenames:
        # Construct full path to file within the specific audience directory
        filepath = os.path.join(audience_data_dir, filename)
        print(f"LOG: [generate_answer] Reading relevant file: {filepath}") # ADDED LOG
        content = read_file_content(filepath)
        if content:
            # Extract metadata from document
            url, title = extract_document_metadata(content)
            document_metadata[filename] = {
                "url": url or "",
                "title": title or filename.replace('.md', '').replace('-', ' ').title()
            }
            print(f"LOG: [generate_answer] Extracted metadata for {filename}: URL={url is not None}, Title={title is not None}")
            
            final_context_parts.append(
                f"--- Dokument: {filename} ---\\n{content}")
        else:
            print(
                f"Warning: Could not read relevant file {filename} from {audience_data_dir} for final context."
            )
            # Still add to metadata with fallback values
            document_metadata[filename] = {
                "url": "",
                "title": filename.replace('.md', '').replace('-', ' ').title()
            }

    if not final_context_parts:
        print("Error: [generate_answer] Could not build final context (all relevant files failed to read).") # ADDED LOG
        return ChatbotResponse(
            message=
            "Ett fel uppstod: Kunde inte läsa innehållet i de relevanta dokumenten.",
            source_links=[],
            source_names=[],
        )

    final_context = "\\n\\n".join(final_context_parts)

    print("\\n--- Calling LLM 2 for Final Answer JSON ---")
    llm2_prompt = format_llm2_prompt(user_query, final_context, document_metadata)

    if DEBUG:
        print("-" * 20 + " LLM 2 (JSON Generation) - START " + "-" * 20)
        if len(llm2_prompt) > 1000:
            print(
                f"Prompt preview:\\n{llm2_prompt[:500]}...\\n...{llm2_prompt[-500:]}"
            )
        else:
            print(f"Prompt:\\n{llm2_prompt}")

    llm_response_text = ""
    try:
        response = model.generate_content(llm2_prompt)
        llm_response_text = response.text.strip()

        if DEBUG:
            print(
                f"LLM 2 Raw Response Text (Expecting JSON):\\n{llm_response_text}"
            )

        # Attempt to find JSON block
        json_string = None
        json_match = re.search(r"```(?:json)?\\s*(\\{.*?\\})\\s*```",
                               llm_response_text, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_string = json_match.group(1)
            if DEBUG: print("LOG: Extracted JSON using regex from markdown block.") # UPDATED LOG
        else:
            # If regex fails, try finding first '{' and last '}'
            try:
                start_index = llm_response_text.index('{')
                end_index = llm_response_text.rindex('}')
                json_string = llm_response_text[start_index:end_index + 1]
                if DEBUG: print("LOG: Extracted JSON using first '{' and last '}'.") # ADDED LOG
            except ValueError: # Handle cases where '{' or '}' are not found
                pass # json_string remains None

        # Check if we successfully extracted a string
        if json_string is None:
            print(f"Error: [generate_answer] Failed to extract JSON block from raw response. Raw response:\\n{llm_response_text}")
            raise ValueError("Could not extract a potential JSON object from LLM 2 response.")

        # Log the exact string before parsing
        if DEBUG:
            print(f"LOG: Attempting to parse JSON string:\n{json_string}")

        # Parse and validate
        response_data = ChatbotResponse.model_validate_json(json_string)
        print("LOG: [generate_answer] Successfully parsed JSON from LLM 2.")
        
        # Ensure all source_names are truncated to 30 characters (validator should handle this, but explicit check)
        response_data.source_names = [truncate_citation_name(name) for name in response_data.source_names]

        # Fallback: If LLM provided a meaningful answer but no citations, add them from metadata
        error_indicators = [
            "kunde inte hitta",
            "ingen relevant",
            "inget relevant",
            "could not find",
            "no relevant"
        ]
        message_lower = response_data.message.lower()
        is_error_message = any(indicator in message_lower for indicator in error_indicators)
        
        # Apply fallback only if:
        # 1. LLM provided no citations (empty lists)
        # 2. We have relevant documents with metadata
        # 3. The message is not an error message (meaningful answer was provided)
        if (not response_data.source_links and not response_data.source_names) and document_metadata and not is_error_message:
            print("LOG: [generate_answer] LLM provided answer but no citations, using extracted metadata as fallback.")
            fallback_links = []
            fallback_names = []
            
            # Use all relevant documents' metadata as citations
            for filename in relevant_filenames:
                meta = document_metadata.get(filename, {})
                url = meta.get("url", "").strip()
                title = meta.get("title", "").strip()
                
                if url:  # Only add if we have a URL
                    fallback_links.append(url)
                    # Extract clean title (before ' - ' if present)
                    if ' - ' in title:
                        title = title.split(' - ')[0].strip()
                    if not title:
                        title = filename.replace('.md', '').replace('-', ' ').title()
                    # Truncate to 30 characters
                    fallback_names.append(truncate_citation_name(title))
            
            if fallback_links:
                response_data.source_links = fallback_links
                response_data.source_names = fallback_names
                print(f"LOG: [generate_answer] Applied fallback citations: {len(fallback_links)} sources")
        elif len(response_data.source_links) != len(response_data.source_names):
            # Fix mismatch in citation arrays
            print("LOG: [generate_answer] Warning: source_links and source_names length mismatch, fixing...")
            min_len = min(len(response_data.source_links), len(response_data.source_names))
            response_data.source_links = response_data.source_links[:min_len]
            response_data.source_names = response_data.source_names[:min_len]

        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - SUCCESS " + "-" * 20)
        return response_data

    except (ValidationError, json.JSONDecodeError) as json_val_error:
        print(f"Error parsing/validating JSON from LLM 2: {json_val_error}")
        print(f"LLM 2 Raw Response Text was:\\n{llm_response_text}")
        if DEBUG:
            print("-" * 20 +
                  " LLM 2 (JSON Generation) - PARSE/VALIDATE FAILED " +
                  "-" * 20)
        return ChatbotResponse(
            message=
            "Jag är ledsen, ett internt fel uppstod när svaret skulle bearbetas.",
            source_links=[],
            source_names=[],
        )

    except Exception as e:
        print(f"Error during LLM 2 call or processing: {e}")
        print(f"LLM 2 Raw Response Text was:\\n{llm_response_text}")
        if DEBUG:
            print("-" * 20 + " LLM 2 (JSON Generation) - GENERAL FAILED " +
                  "-" * 20)
        return ChatbotResponse(
            message=
            "Jag är ledsen, ett oväntat fel inträffade när svaret genererades.",
            source_links=[],
            source_names=[],
        )


# --- Helper function for parallel batch processing ---
def process_single_batch(batch_filenames: List[str], user_query: str,
                         base_data_dir: str, audience: str, # Added audience
                         model: genai.GenerativeModel,
                         batch_num: int, total_batches: int) -> List[str]:
    """Processes a single batch: reads files, calls LLM 1, parses results."""
    script_dir = os.path.dirname(__file__)
    # Construct audience-specific path: backend/data/{audience}
    audience_data_dir = os.path.join(script_dir, base_data_dir, audience)
    print(
        f"LOG: [process_single_batch {batch_num}/{total_batches}] Using audience data directory: {audience_data_dir}" # ADDED LOG
    )
    print(
        f"\\n>>> Starting Batch {batch_num}/{total_batches} ({len(batch_filenames)} files) [Threaded] <<<"
    )

    # Read content for the current batch from the audience directory
    batch_content: List[Tuple[str, str]] = []
    print(f"Reading content for batch {batch_num} from {audience_data_dir}...")
    for filename in batch_filenames:
        # Construct full path to file within the specific audience directory
        filepath = os.path.join(audience_data_dir, filename)
        content = read_file_content(filepath) # read_file_content already logs path
        if content:
            batch_content.append((filename, content))
        else:
            print(
                f"Warning: Skipping file {filename} in batch {batch_num} from {audience_data_dir} due to read error."
            )

    if not batch_content:
        print(
            f"Warning: Skipping batch {batch_num} as no content could be read from {audience_data_dir}."
        )
        return []

    print(f"Content read for batch {batch_num}. Sending to LLM 1...")

    # Format prompt and call LLM 1
    llm1_prompt = format_llm1_batch_prompt(user_query, batch_content)
    llm1_response_text = call_llm_1_relevance_batch(model, llm1_prompt)

    # Parse response
    batch_actual_filenames = [fn for fn, _ in batch_content] # Filenames only, without path
    relevant_in_batch = parse_llm1_response(llm1_response_text,
                                            batch_actual_filenames)

    print(
        f"<<< Finished Batch {batch_num}/{total_batches}. Found {len(relevant_in_batch)} relevant files. [Threaded] >>>"
    )
    if DEBUG and relevant_in_batch:
        print(f"Relevant files in batch {batch_num}: {relevant_in_batch}")

    return relevant_in_batch


# --- Main Pipeline Function ---


def run_new_cag_pipeline(user_query: str, audience: str) -> str: # Added audience
    """
    Runs the new CAG pipeline using parallel batch processing for a specific audience.
    Returns a JSON string matching the frontend format.
    """
    print(f"\\n--- Starting New CAG Pipeline for Query: '{user_query}', Audience: '{audience}' ---") # UPDATED LOG

    # 1. List documents from the specific audience directory
    # Pass base DATA_DIR and the specific audience
    all_filenames = get_document_filenames(DATA_DIR, audience)
    if not all_filenames:
        # Log already happened in get_document_filenames
        error_response = ChatbotResponse(
            message=f"Kunde inte hitta några dokument att bearbeta för målgruppen '{audience}'.", # More specific error
            source_links=[],
            source_names=[])
        return error_response.model_dump_json(indent=2)

    total_files = len(all_filenames)
    print(f"Found {total_files} documents to process for audience '{audience}'.")

    # 2. Process in batches with LLM 1
    aggregated_relevant_filenames: Set[str] = set()
    num_batches = math.ceil(total_files / BATCH_SIZE)
    # No need for full_data_dir here, it's constructed in process_single_batch

    batches = []
    for i in range(num_batches):
        start_index = i * BATCH_SIZE
        end_index = min(start_index + BATCH_SIZE, total_files)
        batches.append(all_filenames[start_index:end_index])

    print(
        f"Processing documents in {num_batches} batches of up to {BATCH_SIZE} files each using up to {MAX_WORKERS} parallel workers."
    )

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_WORKERS) as executor:
        future_to_batch_num = {
            executor.submit(
                process_single_batch,
                batch_filenames,
                user_query,
                DATA_DIR,       # Pass base data dir
                audience,       # Pass audience
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

    print(f"\\n--- Aggregation Complete ---")
    print(
        f"Total relevant files identified by LLM 1 across all batches: {len(aggregated_relevant_filenames)}"
    )
    if DEBUG and aggregated_relevant_filenames:
        print(f"Aggregated relevant filenames: {sorted(list(aggregated_relevant_filenames))}") # ADDED LOG

    # 3. Call LLM 2 with relevant filenames and audience
    final_response_object: ChatbotResponse = generate_answer(
        llm2_model, user_query, sorted(list(aggregated_relevant_filenames)),
        DATA_DIR, audience) # Pass audience

    print("\\n--- New CAG Pipeline Complete ---")

    return final_response_object.model_dump_json(indent=2)


# --- Request Body Model ---
class ChatRequest(BaseModel):
    query: str
    audience: str # Added audience field


# --- API Endpoint ---
@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    """
    API endpoint to handle chat requests.
    Takes a user query and audience, runs the pipeline, and returns the JSON string.
    """
    user_query = chat_request.query
    audience = chat_request.audience # Get audience from request

    # Basic validation
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if not audience or audience not in ["invanare", "personal"]:
        print(f"Error: Invalid audience received: {audience}") # ADDED LOG
        raise HTTPException(status_code=400, detail=f"Invalid audience specified: {audience}")

    print(f"\\n--- Received API Request --- Query: '{user_query}', Audience: '{audience}' ---") # UPDATED LOG

    try:
        # Run the pipeline function with query and audience
        response_json_str = run_new_cag_pipeline(user_query, audience)

        # Parse the JSON string back to return as JSON response
        response_data = json.loads(response_json_str)

        print("\\n--- API Request Processing Complete ---")
        return JSONResponse(content=response_data)

    except Exception as e:
        print(f"Error processing API request in endpoint: {e}")
        import traceback
        traceback.print_exc()
        # Log specific audience for context
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error processing chat request for audience '{audience}'.")

# --- Journal Data Endpoint ---
JOURNAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "journal", "patient_data.json")

@app.get("/api/journal")
async def get_journal_data():
    """
    API endpoint to retrieve patient journal data.
    In a real application, this would require authentication and return user-specific data.
    """
    print(f"LOG: [get_journal_data] Attempting to read journal data from: {JOURNAL_DATA_PATH}")
    
    if not os.path.isfile(JOURNAL_DATA_PATH):
        print(f"Error: Journal data file not found at {JOURNAL_DATA_PATH}")
        raise HTTPException(status_code=404, detail="Journal data not found")
    
    try:
        with open(JOURNAL_DATA_PATH, 'r', encoding='utf-8') as f:
            journal_data = json.load(f)
        return JSONResponse(content=journal_data)
    except Exception as e:
        print(f"Error reading journal data: {e}")
        raise HTTPException(status_code=500, detail="Failed to read journal data")


# --- Chat with Journal Context Endpoint ---
class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatWithJournalRequest(BaseModel):
    query: str
    audience: str
    journal_data: Optional[dict] = None  # Optional journal data for personalized responses
    clarification_round: int = 0  # Track how many clarification rounds have occurred (0-2)
    conversation_history: List[ConversationMessage] = []  # Previous messages for context
    is_follow_up: bool = False  # Whether this is a follow-up to a previous question
    last_relevant_docs: List[str] = []  # Cached relevant documents from previous question

@app.post("/api/chat-with-journal")
async def chat_with_journal_endpoint(chat_request: ChatWithJournalRequest):
    """
    API endpoint to handle chat requests with optional journal context.
    When journal_data is provided, the response will be personalized using the patient's medical history.
    Supports up to 2 rounds of clarifying questions before providing a final answer.
    For follow-up questions, skips document search (LLM1) and reuses cached relevant docs.
    """
    user_query = chat_request.query
    audience = chat_request.audience
    journal_data = chat_request.journal_data
    clarification_round = chat_request.clarification_round
    conversation_history = chat_request.conversation_history
    is_follow_up = chat_request.is_follow_up
    last_relevant_docs = chat_request.last_relevant_docs

    # Basic validation
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if not audience or audience not in ["invanare", "personal"]:
        print(f"Error: Invalid audience received: {audience}")
        raise HTTPException(status_code=400, detail=f"Invalid audience specified: {audience}")

    print(f"\n--- Received API Request (with journal) --- Query: '{user_query}', Audience: '{audience}', Has Journal: {journal_data is not None}, Clarification Round: {clarification_round}, Is Follow-up: {is_follow_up} ---")

    try:
        # If journal data is provided, run the personalized pipeline
        if journal_data:
            response_json_str = run_personalized_pipeline(
                user_query, audience, journal_data, 
                clarification_round=clarification_round,
                conversation_history=conversation_history,
                is_follow_up=is_follow_up,
                last_relevant_docs=last_relevant_docs
            )
        else:
            # Fall back to the regular pipeline
            response_json_str = run_new_cag_pipeline(user_query, audience)

        response_data = json.loads(response_json_str)

        print("\n--- API Request Processing Complete ---")
        return JSONResponse(content=response_data)

    except Exception as e:
        print(f"Error processing API request in endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error processing chat request for audience '{audience}'.")


def format_journal_context(journal_data: dict) -> str:
    """Formats journal data into a readable context string for the LLM."""
    context_parts = []
    
    if "labs_and_exams" in journal_data:
        data = journal_data["labs_and_exams"]
        
        # Youth history - important for fracture history etc.
        if "youth" in data:
            youth = data["youth"]
            context_parts.append("=== UNGDOMSHISTORIK ===")
            if "labs" in youth:
                labs = youth["labs"]
                vals_str = ", ".join([f"{k}={v}" for k, v in labs.items()])
                context_parts.append(f"Labvärden (ungdom): {vals_str}")
            if "imaging" in youth:
                context_parts.append("Tidigare frakturer och skador:")
                for key, value in youth["imaging"].items():
                    # Parse age from key (e.g., "nyckelbensfraktur_19" -> 19 år)
                    parts = key.rsplit('_', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        injury_name = parts[0].replace('_', ' ').capitalize()
                        age = parts[1]
                        context_parts.append(f"  - {injury_name} ({age} års ålder): {value}")
                    else:
                        context_parts.append(f"  - {key}: {value}")
        
        # Adult initial values
        if "adult" in data:
            adult = data["adult"]
            context_parts.append("\n=== VUXEN (INITIAL BEDÖMNING) ===")
            if "labs_initial" in adult:
                labs = adult["labs_initial"]
                vals_str = ", ".join([f"{k}={v}" for k, v in labs.items()])
                context_parts.append(f"Initiala labvärden: {vals_str}")
            if "ekg" in adult:
                context_parts.append(f"EKG: {adult['ekg']}")
        
        # Current status
        if "current" in data:
            current = data["current"]
            context_parts.append("\n=== AKTUELLA VÄRDEN ===")
            if "labs" in current:
                labs = current["labs"]
                vals_str = ", ".join([f"{k}={v}" for k, v in labs.items()])
                context_parts.append(f"Aktuella labvärden: {vals_str}")
            if "ekg" in current:
                context_parts.append(f"EKG: {current['ekg']}")
            if "lungröntgen" in current:
                context_parts.append(f"Lungröntgen: {current['lungröntgen']}")
            if "eko" in current:
                context_parts.append(f"Ekokardiografi: {current['eko']}")
        
        # Cardiometabolic history
        if "cardiometabolic" in data:
            context_parts.append("\n=== HJÄRT-KÄRL OCH METABOLISM (HISTORIK) ===")
            for period, values in data["cardiometabolic"].items():
                period_name = period.replace("_", " ")
                vals_str = ", ".join([f"{k}={v}" for k, v in values.items()])
                context_parts.append(f"{period_name}: {vals_str}")
        
        # Cognitive assessment
        if "cognitive" in data:
            cog = data["cognitive"]
            context_parts.append("\n=== KOGNITIV BEDÖMNING ===")
            if "labs" in cog:
                labs = cog["labs"]
                vals_str = ", ".join([f"{k}={v}" for k, v in labs.items()])
                context_parts.append(f"Labvärden: {vals_str}")
            if "MMT" in cog:
                context_parts.append(f"MMT: {cog['MMT']}/30")
            if "clock_test" in cog:
                context_parts.append(f"Klocktest: {cog['clock_test']}")
            if "MRT" in cog:
                context_parts.append(f"MRT: {cog['MRT']}")
        
        # Orthopedics - Knee
        if "knee_arthrosis_period" in data:
            knee = data["knee_arthrosis_period"]
            context_parts.append("\n=== ORTOPEDI (KNÄ) ===")
            if "xray" in knee:
                context_parts.append(f"Knäröntgen: {knee['xray']}")
            if "postop" in knee:
                context_parts.append(f"Postoperativ knäprotes: {knee['postop']}")
        
        # Urology
        if "urology" in data:
            uro = data["urology"]
            context_parts.append("\n=== UROLOGI ===")
            if "PSA_trend" in uro:
                context_parts.append(f"PSA-trend: {' → '.join(map(str, uro['PSA_trend']))}")
            if "urine" in uro:
                context_parts.append(f"Urinprov: {uro['urine']}")
            if "ultrasound" in uro:
                context_parts.append(f"Ultraljud prostata: {uro['ultrasound']}")
    
    return "\n".join(context_parts)


def format_llm2_prompt_with_journal(user_query: str, relevant_context: str, journal_context: str, 
                                     clarification_round: int = 0, conversation_history: List[Dict] = None,
                                     must_answer: bool = False) -> str:
    """
    Formats the prompt for the second LLM with both public 1177 content and patient journal data.
    Supports clarifying questions when the query is ambiguous.
    """
    # Build conversation history section if available
    history_section = ""
    is_follow_up_context = False
    original_topic = ""
    if conversation_history and len(conversation_history) > 0:
        is_follow_up_context = True
        # Extract the original topic from the first user message
        for msg in conversation_history:
            if msg.get("role") == "user":
                original_topic = msg.get("content", "")
                break
        
        history_section = "\n=== TIDIGARE KONVERSATION (VIKTIGT - KONTEXT FÖR UPPFÖLJNINGSFRÅGOR) ===\n"
        history_section += f"URSPRUNGLIGT ÄMNE: \"{original_topic}\"\n"
        history_section += "Användaren ställer en UPPFÖLJNINGSFRÅGA. Du MÅSTE:\n"
        history_section += "1. Svara baserat på SAMMA ÄMNE som den ursprungliga frågan\n"
        history_section += "2. Endast använda källor som är DIREKT relevanta för det ursprungliga ämnet\n"
        history_section += "3. IGNORERA dokument som handlar om andra ämnen (även om de finns i kontexten)\n\n"
        history_section += "Konversationshistorik:\n"
        for msg in conversation_history:
            role = "Användare" if msg.get("role") == "user" else "Assistent"
            history_section += f"{role}: {msg.get('content', '')}\n"
        history_section += "\n"
    
    # Clarification instructions based on round
    clarification_instructions = ""
    if must_answer or clarification_round >= 2:
        clarification_instructions = """
VIKTIGT: Du har redan ställt förtydligande frågor. Du MÅSTE nu ge ett svar med de bästa 1-3 källorna baserat på tillgänglig information. Ställ INGA fler frågor."""
    else:
        clarification_instructions = f"""
FÖRTYDLIGANDE FRÅGOR (Omgång {clarification_round + 1} av max 2):
Om användarens fråga är otydlig eller kan ha flera olika tolkningar (t.ex. "ont i armen" kan bero på många olika saker), BÖR du ställa en förtydligande fråga MED FÄRDIGA SVARSALTERNATIV.

När du ställer en förtydligande fråga, sätt "needs_clarification" till true och fyll i "clarifying_question" och "clarifying_options".
Alternativen ska vara konkreta och relevanta för frågan (max 4 alternativ).

Exempel på bra förtydligande frågor:
- "Kan du beskriva smärtan närmare?" med alternativ: A) Skarp/stickande, B) Molande/dov, C) Brännande, D) Krampartad
- "När började smärtan?" med alternativ: A) Efter en skada/fall, B) Gradvis utan orsak, C) Plötsligt utan orsak
- "Var sitter smärtan?" med alternativ: A) Överarmen, B) Armbågen, C) Underarmen, D) Handleden

Ställ ENDAST förtydligande frågor om det verkligen behövs för att ge ett bra svar. Om du kan ge ett bra svar direkt, gör det."""

    prompt = f"""Du är en hjälpsam AI-assistent för 1177 Vårdguiden. Du har tillgång till två typer av information:

1. ALLMÄN MEDICINSK INFORMATION från 1177.se (nedan under "Tillhandahållen Kontext")
2. PATIENTENS PERSONLIGA JOURNALDATA (nedan under "Patientens Journal")

Din uppgift är att ge ett PERSONLIGT och relevant svar som kombinerar:
- Allmän medicinsk information från 1177.se
- Personliga insikter baserade på patientens medicinska historik
{clarification_instructions}

VIKTIGT: När patientens journal innehåller relevant information för frågan (t.ex. tidigare frakturer, labvärden, diagnoser), MÅSTE du referera till denna personliga historik i ditt svar.

Svara ALLTID med ett JSON-objekt, och inget annat.

OM DU GER ETT SVAR (needs_clarification = false):
{{
  "message": "Ett tydligt och koncist svar på användarens fråga.",
  "source_links": ["MAX 3-4 URL-källor. Hämta URL:en från 'URL Source:' i varje dokument."],
  "source_names": ["MAX 3-4 korta namn (max 30 tecken). Hämta från 'Title:' i varje dokument."],
  "needs_clarification": false,
  "clarifying_question": null,
  "clarifying_options": []
}}

OM DU BEHÖVER STÄLLA EN FÖRTYDLIGANDE FRÅGA (max {2 - clarification_round} gånger till):
{{
  "message": "Din förtydligande fråga här (t.ex. 'För att ge dig ett bättre svar behöver jag veta mer. Var sitter smärtan?')",
  "source_links": [],
  "source_names": [],
  "needs_clarification": true,
  "clarifying_question": "Din förtydligande fråga här",
  "clarifying_options": [
    {{"id": "A", "text": "Alternativ 1"}},
    {{"id": "B", "text": "Alternativ 2"}},
    {{"id": "C", "text": "Alternativ 3"}}
  ]
}}

VIKTIGT OM FÖRTYDLIGANDE FRÅGOR:
- När du ställer en förtydligande fråga, inkludera ALDRIG några källor/referenser
- source_links och source_names MÅSTE vara tomma listor []
- Referenser ska ENDAST visas i det SLUTGILTIGA svaret efter att du har samlat tillräcklig information

KRITISKA REGLER:
- När needs_clarification är true: source_links och source_names MÅSTE vara tomma listor []
- När needs_clarification är false: Inkludera MAXIMALT 3-4 källor - välj de MEST relevanta för ÄMNET
- Om du inte kan avgöra vilka källor som är mest relevanta, STÄLL EN FÖRTYDLIGANDE FRÅGA (utan källor!)
- ALDRIG säg "Du kan läsa mer på 1177.se" utan att inkludera den specifika URL:en
- Basera svaret på den givna kontexten. Hitta inte på information.
- Om patientens journal innehåller relevant historik, NÄMN DEN i svaret

REGLER FÖR UPPFÖLJNINGSFRÅGOR (om det finns TIDIGARE KONVERSATION):
- HÅLL DIG TILL ÄMNET från den ursprungliga frågan
- Välj ENDAST källor som är relevanta för det ursprungliga ämnet
- IGNORERA dokument om andra ämnen även om de finns i kontexten
- Exempel: Om första frågan handlade om DEMENS, använd INTE källor om cancer, hudsjukdomar eller annat orelaterat
{history_section}
Användarens Fråga: "{user_query}"

=== PATIENTENS PERSONLIGA JOURNAL ===
{journal_context}

=== ALLMÄN INFORMATION FRÅN 1177.SE ===
{relevant_context}

JSON Svar:
"""
    return prompt


def run_personalized_pipeline(user_query: str, audience: str, journal_data: dict,
                              clarification_round: int = 0, 
                              conversation_history: List[Any] = None,
                              is_follow_up: bool = False,
                              last_relevant_docs: List[str] = None) -> str:
    """
    Runs the CAG pipeline with personalized journal context.
    Supports up to 2 rounds of clarifying questions before providing a final answer.
    For follow-up questions, skips LLM1 document search and reuses cached relevant docs.
    """
    if conversation_history is None:
        conversation_history = []
    if last_relevant_docs is None:
        last_relevant_docs = []
    
    # Convert conversation history to dict format for the prompt
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in conversation_history] if conversation_history else []
    
    # Determine if we must provide an answer (no more clarifications allowed)
    must_answer = clarification_round >= 2
    
    print(f"\n--- Starting Personalized CAG Pipeline for Query: '{user_query}', Audience: '{audience}', Round: {clarification_round}, Must Answer: {must_answer}, Is Follow-up: {is_follow_up} ---")

    # Format journal data into readable context
    journal_context = format_journal_context(journal_data)
    print(f"LOG: Formatted journal context ({len(journal_context)} characters)")

    # 1. List documents from the specific audience directory
    all_filenames = get_document_filenames(DATA_DIR, audience)
    if not all_filenames:
        # Even without public docs, we can still answer with journal data
        print("Warning: No public documents found, using only journal data")
        
        # Create a response using only journal context
        prompt = format_llm2_prompt_with_journal(
            user_query, "Inga offentliga dokument tillgängliga.", journal_context,
            clarification_round=clarification_round, conversation_history=history_dicts, must_answer=must_answer
        )
        try:
            response = llm2_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON from response
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_string = json_match.group(1)
            else:
                try:
                    start_index = response_text.index('{')
                    end_index = response_text.rindex('}')
                    json_string = response_text[start_index:end_index + 1]
                except ValueError:
                    json_string = None
            
            if json_string:
                response_data = ChatbotResponse.model_validate_json(json_string)
                return response_data.model_dump_json(indent=2)
        except Exception as e:
            print(f"Error generating journal-only response: {e}")
        
        error_response = ChatbotResponse(
            message="Kunde inte bearbeta din förfrågan. Vänligen försök igen.",
            source_links=[],
            source_names=[])
        return error_response.model_dump_json(indent=2)

    total_files = len(all_filenames)
    print(f"Found {total_files} documents to process for audience '{audience}'.")

    # 2. For follow-up questions, SKIP LLM1 and reuse cached relevant docs
    aggregated_relevant_filenames: Set[str] = set()
    
    if is_follow_up and last_relevant_docs:
        # SKIP LLM1 - reuse cached relevant documents for faster follow-up responses
        print(f"FOLLOW-UP: Skipping LLM1 document search, reusing {len(last_relevant_docs)} cached relevant docs")
        aggregated_relevant_filenames = set(last_relevant_docs)
    else:
        # Normal flow: Process in batches with LLM 1
        num_batches = math.ceil(total_files / BATCH_SIZE)

        batches = []
        for i in range(num_batches):
            start_index = i * BATCH_SIZE
            end_index = min(start_index + BATCH_SIZE, total_files)
            batches.append(all_filenames[start_index:end_index])

        print(f"Processing documents in {num_batches} batches.")

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_batch_num = {
                executor.submit(
                    process_single_batch,
                    batch_filenames,
                    user_query,
                    DATA_DIR,
                    audience,
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
    print(f"Total relevant files: {len(aggregated_relevant_filenames)}")

    # 3. Build context from relevant documents and extract metadata
    script_dir = os.path.dirname(__file__)
    audience_data_dir = os.path.join(script_dir, DATA_DIR, audience)
    
    final_context_parts = []
    document_metadata = {}  # Store metadata for fallback: filename -> {url, title}
    
    for filename in sorted(list(aggregated_relevant_filenames)):
        filepath = os.path.join(audience_data_dir, filename)
        content = read_file_content(filepath)
        if content:
            final_context_parts.append(f"--- Dokument: {filename} ---\n{content}")
            # Extract metadata from document
            url, title = extract_document_metadata(content)
            document_metadata[filename] = {
                "url": url or "",
                "title": title or filename.replace('.md', '').replace('-', ' ').title()
            }
            print(f"LOG: [run_personalized_pipeline] Extracted metadata for {filename}: URL={url is not None}, Title={title is not None}")

    final_context = "\n\n".join(final_context_parts) if final_context_parts else "Inga relevanta dokument hittades."

    # 4. Call LLM 2 with both contexts
    print("\n--- Calling LLM 2 for Personalized Answer ---")
    llm2_prompt = format_llm2_prompt_with_journal(
        user_query, final_context, journal_context,
        clarification_round=clarification_round, conversation_history=history_dicts, must_answer=must_answer
    )

    try:
        response = llm2_model.generate_content(llm2_prompt)
        response_text = response.text.strip()

        if DEBUG:
            print(f"LLM 2 Raw Response:\n{response_text[:500]}...")

        # Parse JSON
        json_string = None
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_string = json_match.group(1)
        else:
            try:
                start_index = response_text.index('{')
                end_index = response_text.rindex('}')
                json_string = response_text[start_index:end_index + 1]
            except ValueError:
                pass

        if json_string:
            response_data = ChatbotResponse.model_validate_json(json_string)
            
            # CRITICAL: When asking clarifying questions, NEVER include sources
            if response_data.needs_clarification:
                response_data.source_links = []
                response_data.source_names = []
                # Include relevant docs for caching (so follow-ups can reuse them)
                response_data.relevant_docs = sorted(list(aggregated_relevant_filenames))
                print("LOG: [run_personalized_pipeline] Clarifying question - cleared all sources, cached relevant docs")
                print("\n--- Personalized Pipeline Complete (Clarification) ---")
                return response_data.model_dump_json(indent=2)
            
            # Truncate source names and limit to max 4
            response_data.source_names = [truncate_citation_name(name) for name in response_data.source_names][:4]
            response_data.source_links = response_data.source_links[:4]
            
            # Fallback: If LLM provided a meaningful answer but no citations, add them from metadata
            error_indicators = [
                "kunde inte hitta",
                "ingen relevant",
                "inget relevant",
                "could not find",
                "no relevant"
            ]
            message_lower = response_data.message.lower()
            is_error_message = any(indicator in message_lower for indicator in error_indicators)
            
            # Detect journal-specific queries - don't apply fallback for these
            journal_query_indicators = [
                "min journal", "mina journal", "min sjukhistoria", "mina sjukhistoria",
                "mina labvärden", "mitt labvärde", "mina värden", "mina provsvar",
                "sammanfatta min", "sammanfatta mina", "min medicinska", "mina medicinska",
                "min historik", "mina historik", "baserat på min journal", "enligt min journal",
                "vad säger min journal", "vad visar min journal", "min hälsa", "mina diagnoser"
            ]
            query_lower = user_query.lower()
            is_journal_specific_query = any(indicator in query_lower for indicator in journal_query_indicators)
            
            if is_journal_specific_query:
                print("LOG: [run_personalized_pipeline] Journal-specific query detected - skipping fallback citations")
            
            # Apply fallback only if:
            # 1. LLM provided no citations (empty lists)
            # 2. We have relevant documents with metadata
            # 3. The message is not an error message (meaningful answer was provided)
            # 4. NOT a journal-specific query (those don't need 1177.se sources)
            if (not response_data.source_links and not response_data.source_names) and document_metadata and not is_error_message and not is_journal_specific_query:
                print("LOG: [run_personalized_pipeline] LLM provided answer but no citations, using extracted metadata as fallback.")
                fallback_links = []
                fallback_names = []
                
                # Use all relevant documents' metadata as citations
                for filename in sorted(list(aggregated_relevant_filenames)):
                    meta = document_metadata.get(filename, {})
                    url = meta.get("url", "").strip()
                    title = meta.get("title", "").strip()
                    
                    if url:  # Only add if we have a URL
                        fallback_links.append(url)
                        # Extract clean title (before ' - ' if present)
                        if ' - ' in title:
                            title = title.split(' - ')[0].strip()
                        if not title:
                            title = filename.replace('.md', '').replace('-', ' ').title()
                        # Truncate to 30 characters
                        fallback_names.append(truncate_citation_name(title))
                
                if fallback_links:
                    # Limit to max 4 sources
                    response_data.source_links = fallback_links[:4]
                    response_data.source_names = fallback_names[:4]
                    print(f"LOG: [run_personalized_pipeline] Applied fallback citations: {len(response_data.source_links)} sources (limited to 4)")
            
            # Include relevant docs for caching (so follow-ups can reuse them)
            response_data.relevant_docs = sorted(list(aggregated_relevant_filenames))
            print(f"LOG: [run_personalized_pipeline] Returning {len(response_data.relevant_docs)} relevant docs for caching")
            
            print("\n--- Personalized Pipeline Complete ---")
            return response_data.model_dump_json(indent=2)
        else:
            raise ValueError("Could not extract JSON from response")

    except Exception as e:
        print(f"Error in personalized pipeline: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = ChatbotResponse(
            message="Ett fel uppstod vid bearbetning av din förfrågan.",
            source_links=[],
            source_names=[])
        return error_response.model_dump_json(indent=2)


# Remove the old __main__ block if it exists
