import os
import json
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai  # Renamed to avoid collision with the model
from pydantic import ValidationError
from models import ChatbotResponse, SourceSection # Assuming models.py is in the same directory

# Load environment variables from .env file in the current directory (backend/)
load_dotenv() 
api_key = os.getenv("GOOGLE_API_KEY")

# Check if API key is loaded
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Make sure it's set in backend/.env")

genai.configure(api_key=api_key)

# Using gemini-1.5-flash-latest as specified
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

def get_documents(data_dir="data") -> List[dict]:
    """
    Loads Markdown documents from the specified directory (relative to main.py), 
    splits them into sections, and returns a list of dictionaries, one for each section.
    Expects the data directory to be in the same directory as main.py.
    """
    documents = []
    # Ensure the data directory path is correct relative to this script's location
    script_dir = os.path.dirname(__file__) 
    full_data_dir = os.path.join(script_dir, data_dir)

    if not os.path.isdir(full_data_dir):
        print(f"Error: Data directory not found at {full_data_dir}")
        return documents # Return empty list if directory doesn't exist

    for filename in os.listdir(full_data_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(full_data_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Improved splitting logic to handle potential missing link or title variations
                    lines = content.split('\n')
                    title = "Untitled"
                    link = None
                    content_start_index = 0

                    if lines[0].startswith("# "):
                        title = lines[0][2:].strip()
                        content_start_index = 1
                        if len(lines) > 1 and lines[1].startswith("[") and lines[1].endswith("]"):
                           # Extract URL from markdown link format [url]
                           link_text = lines[1][1:-1].strip()
                           if link_text.startswith("http://") or link_text.startswith("https://"):
                               link = link_text
                           content_start_index = 2 # Content starts after title and link
                        elif len(lines) > 1 and (lines[1].startswith("http://") or lines[1].startswith("https://")):
                            # Handle plain URL on the second line
                            link = lines[1].strip()
                            content_start_index = 2 # Content starts after title and link


                    full_content = '\n'.join(lines[content_start_index:]).strip()
                    
                    # Split content by "## " while keeping the delimiter
                    # We look for lines starting with "## "
                    sections = []
                    current_section = ""
                    for line in full_content.split('\n'):
                        if line.startswith("## "):
                            if current_section: # Add the previous section if it exists
                                sections.append(current_section.strip())
                            current_section = line # Start new section
                        else:
                            current_section += "\n" + line
                    if current_section: # Add the last section
                         sections.append(current_section.strip())

                    # If no "## " sections found, treat the whole content as one section
                    if not sections and full_content:
                       sections.append(full_content)


                    for section_content in sections:
                         if section_content: # Ensure section is not empty
                            documents.append({
                                "title": title,
                                "link": link,
                                "content": section_content,
                            })
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    return documents


def retrieve_relevant_sections(
    user_query: str, documents: List[dict]
) -> List[SourceSection]:
    """
    Uses Gemini to identify relevant sections from the documents.
    """
    if not documents:
        print("No documents provided to retrieve_relevant_sections.")
        return []
        
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    # Constructing the prompt carefully to guide the model
    # Using a clearer JSON structure expectation
    prompt = f"""You are an AI assistant helping to find relevant information from a list of document sections.
User Question: "{user_query}"

Provided Document Sections:
{json.dumps(documents, indent=2)}

Task: Identify the sections most relevant to the user's question. 
Respond ONLY with a JSON object containing a key "relevant_sections". 
The value should be an array of objects. Each object in the array must have the following keys:
- "title": The document title (string).
- "link": The document's link (string or null).
- "content": The content of the relevant section (string).

If no sections are relevant, return an empty array: {"relevant_sections": []}.
Do not include any explanations or introductory text outside the JSON object.

JSON Response:
"""
    try:
        response = model.generate_content(prompt)
        # Attempt to extract JSON even if surrounded by markdown backticks or other text
        raw_response_text = response.text
        json_start = raw_response_text.find('{')
        json_end = raw_response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_response = raw_response_text[json_start:json_end]
            parsed_response = json.loads(json_response)
            relevant_sections_data = parsed_response.get("relevant_sections", [])
            
            # Validate data against Pydantic model
            validated_sections = []
            for section_data in relevant_sections_data:
                try:
                    # Ensure all required fields are present before creating SourceSection
                    if "title" in section_data and "content" in section_data:
                       validated_sections.append(SourceSection(**section_data))
                    else:
                       print(f"Skipping section due to missing fields: {section_data}")
                except ValidationError as ve:
                    print(f"Validation error for section {section_data.get('title', 'N/A')}: {ve}")
            return validated_sections
        else:
            print("Error: Could not find valid JSON in Gemini's response.")
            print(f"Gemini's Raw Response: {raw_response_text}")
            return []

    except json.JSONDecodeError as json_e:
        print(f"Error decoding JSON from Gemini response: {json_e}")
        print(f"Gemini's Raw Response: {raw_response_text}")
        return []
    except Exception as e:
        # Catch other potential errors during generation or processing
        print(f"Error in retrieve_relevant_sections: {e}")
        # Check if 'response' was assigned before the error occurred
        raw_response_text = response.text if 'response' in locals() and hasattr(response, 'text') else 'No response text available'
        print(f"Gemini's Raw Response: {raw_response_text}")
        return []


def generate_answer(user_query: str, relevant_sections: List[SourceSection]) -> ChatbotResponse:
    """
    Uses Gemini to generate a concise answer based on the relevant sections.
    """
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    if not relevant_sections:
        # Handle case where no relevant sections were found
         return ChatbotResponse(
             message="I couldn't find any relevant information in the provided documents to answer your question.", 
             source_links=[], 
             source_titles=[]
        )

    # Prepare context string
    context_parts = []
    source_links_set = set() # Use a set to avoid duplicate links if sections are from the same doc
    source_titles_set = set() # Use a set for titles

    for section in relevant_sections:
        context_parts.append(f"Source Title: {section.title}\nContent:\n{section.content}")
        if section.link:
            source_links_set.add(section.link)
        source_titles_set.add(section.title) # Add title regardless of link presence

    context = "\n\n---\n\n".join(context_parts)
    source_links = list(source_links_set)
    source_titles = list(source_titles_set) # Convert back to list for the response model

    # Constructing the prompt for answer generation
    prompt = f"""You are a helpful AI assistant. Your task is to answer the user's question based *only* on the provided context sections.
Be concise and informative. 
If the context does not contain the answer, state that you cannot answer the question based on the provided information.
Do not make up information.
Cite the source titles relevant to your answer. You can mention them like "(Source: [Title])". Do not include the markdown links like "[Title](link)" in the main answer message itself.

User Question: "{user_query}"

Context Provided:
---
{context}
---

Answer:
"""
    try:
        response = model.generate_content(prompt)
        answer = response.text.strip()

        # Create ChatbotResponse with validated data
        # Pass the collected source titles and links
        return ChatbotResponse(message=answer, source_links=source_links, source_titles=source_titles)

    except Exception as e:
        print(f"Error in generate_answer: {e}")
        # Provide a more informative error message
        return ChatbotResponse(
            message="I'm sorry, an error occurred while generating the answer.", 
            source_links=source_links, # Still include sources if available
            source_titles=source_titles
        )


def main():
    """
    Main function to run the chatbot interaction from the command line.
    Loads documents, gets user query, retrieves sections, generates answer, and prints.
    """
    print("Loading documents...")
    documents = get_documents()
    if not documents:
         print("No documents found or loaded. Exiting.")
         return # Exit if no documents

    print(f"Loaded {len(documents)} sections.")
    
    try:
        user_query = input("Ask your question: ")

        print("\nRetrieving relevant sections...")
        relevant_sections = retrieve_relevant_sections(user_query, documents)

        if relevant_sections:
            print(f"Found {len(relevant_sections)} relevant sections.")
            print("\nGenerating answer...")
            response = generate_answer(user_query, relevant_sections)
        else:
             print("No relevant sections found.")
             # Create a default response if no sections are relevant
             response = ChatbotResponse(
                message="I could not find relevant information to answer your question based on the available documents.",
                source_links=[],
                source_titles=[]
            )


        print("\n--- Chatbot Response ---")
        print("Answer:", response.message)
        # Print unique sources based on title and link combination
        if response.source_links or response.source_titles:
            print("\nSources Used:")
            unique_sources = set()
            # Assuming titles and links correspond if available
            # Create tuples (title, link or None) for uniqueness check
            temp_links = response.source_links + [None] * (len(response.source_titles) - len(response.source_links)) # Pad links if necessary
            
            source_map = {} # Store link by title to handle cases where a title might appear multiple times with/without link
            for title, link in zip(response.source_titles, temp_links):
                if title not in source_map:
                   source_map[title] = link # Keep the first link found for a title

            count = 1
            for title, link in source_map.items():
                 if link:
                     print(f"{count}. {title} ({link})")
                 else:
                     print(f"{count}. {title}")
                 count += 1
        print("------------------------")


    except EOFError:
        print("\nExiting.") # Handle Ctrl+D or end of input stream
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.") # Handle Ctrl+C


if __name__ == "__main__":
    main() 