import os
import re
import json
import requests
from typing import Dict, Any, List, Set, Tuple
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from the .env file in the same directory as the script
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

class JinaReader:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            # Use "x-api-key" for Jina Reader API authentication
            self.headers["x-api-key"] = f"token {api_key}"
            self.headers["Accept"] = "application/json" # Request JSON output

    def read_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL using Jina Reader API
        """
        try:
            # Prepend r.jina.ai/ to the URL for Jina Reader
            reader_url = f"https://r.jina.ai/{url}"
            print(f"Making request to: {reader_url}")

            response = requests.get(
                reader_url,
                headers=self.headers,
                timeout=120 # Add a timeout
            )
            print(f"Status code: {response.status_code}")

            response.raise_for_status()

            # Jina Reader should return JSON if requested via Accept header
            # If it still returns markdown/text, handle it.
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                 data = response.json()
                 # Check if the expected 'data' field with 'content' exists
                 if isinstance(data, dict) and 'data' in data and 'content' in data['data']:
                     return {"text": data['data']['content']}
                 # Fallback if structure is different, maybe {'content': ...} or just text
                 elif isinstance(data, dict) and 'content' in data:
                     return {"text": data['content']}
                 else:
                     # If JSON doesn't contain expected content, try to parse as text
                     print("JSON response received, but 'content' field missing. Trying to use raw text.")
                     return {"text": response.text}

            elif 'text/markdown' in content_type or 'text/plain' in content_type:
                print("Received text/markdown response.")
                return {"text": response.text}
            else:
                print(f"Unexpected Content-Type: {content_type}. Attempting to read as text.")
                return {"text": response.text} # Fallback for unexpected content types

        except requests.Timeout:
             print(f"Timeout occurred while reading URL: {url}")
             return {}
        except requests.RequestException as e:
            print(f"Error reading URL {url}: {e}")
            # Print response body if available and not too large
            if e.response is not None:
                try:
                    response_text = e.response.text
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response body (partial): {response_text[:500]}")
                except Exception as read_err:
                     print(f"Could not read error response body: {read_err}")
            return {}
        except json.JSONDecodeError as e:
             print(f"Error decoding JSON response from {url}: {e}")
             print(f"Response text (partial): {response.text[:500]}")
             # Fallback to using raw text if JSON decoding fails but we got text
             return {"text": response.text}
        except Exception as e: # Catch unexpected errors
            print(f"An unexpected error occurred for URL {url}: {e}")
            return {}


def extract_links(content: str) -> List[Dict[str, str]]:
    """
    Extract all markdown links: [text](url) that are not images
    Process each link individually
    """
    links = []
    
    # This pattern matches markdown links like [text](url "title")
    pattern = r'\[([^\]]+)\]\((https?://[^"\s]+)(?:\s+"[^"]*")?\)'
    matches = re.findall(pattern, content)
    
    for text, url in matches:
        # Basic cleaning of text
        clean_text = text.strip().replace('\n', ' ').replace('\r', '')
        # Remove trailing punctuation from URL if accidentally captured
        url = url.strip().rstrip('.,;:')
        
        # Skip empty text links (may happen with certain formats)
        if not clean_text:
            clean_text = "Unnamed Link"
            
        # Skip image links (links with "Image" in the text or pointing to image files)
        if "Image" in clean_text or url.endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
            continue
            
        links.append({
            "text": clean_text,
            "url": url
        })

    return links


def save_links_to_file(links: List[Dict[str, str]], output_file: str):
    """Saves the list of links to a text file, sorted alphabetically by text."""
    # Sort by link text, case-insensitive
    sorted_links = sorted(links, key=lambda x: x['text'].lower())

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Total unique links found: {len(sorted_links)}\n\n")
            for i, link in enumerate(sorted_links, 1):
                 # Text is already cleaned during extraction
                 f.write(f"{i}. [{link['text']}]: {link['url']}\n")
        print(f"\nLinks saved to {output_file}")
    except IOError as e:
        print(f"Error writing to file {output_file}: {e}")


def extract_fakta_och_rad_links(content: str) -> List[Dict[str, str]]:
    """
    Extract links from the Fakta och råd section (everything above Vanliga patientfrågor)
    """
    # Find the start of the "Fakta och råd" section (after the main header)
    start_pattern = r"Fakta och råd\s+=+"
    start_match = re.search(start_pattern, content)
    
    # Find the start of the "Vanliga patientfrågor" section
    end_pattern = r"Vanliga patientfrågor\s+-+"
    end_match = re.search(end_pattern, content)
    
    if not start_match or not end_match:
        print("Could not find section boundaries for Fakta och råd")
        return []
    
    # Extract the content between these sections
    fakta_content = content[start_match.end():end_match.start()]
    
    # Extract links from this section
    links = extract_links(fakta_content)
    
    # Filter out links that don't contain "fakta" in the URL and deduplicate by URL
    seen_urls = set()
    fakta_links = []
    
    for link in links:
        if "kry.se/fakta" in link["url"] and link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            fakta_links.append(link)
    
    return fakta_links


def extract_vanliga_patientfragor_links(content: str) -> List[Dict[str, str]]:
    """
    Extract links from the Vanliga patientfrågor section
    """
    # Find the start of the "Vanliga patientfrågor" section
    start_pattern = r"Vanliga patientfrågor\s+-+"
    start_match = re.search(start_pattern, content)
    
    # Find the end (which is the "Kry samarbetar med" section)
    end_pattern = r"Kry samarbetar med"
    end_match = re.search(end_pattern, content)
    
    if not start_match:
        print("Could not find section boundaries for Vanliga patientfrågor")
        return []
    
    # If we can't find the end pattern, just go to the end of the content
    if not end_match:
        patient_content = content[start_match.end():]
    else:
        patient_content = content[start_match.end():end_match.start()]
    
    # Extract links from this section
    links = extract_links(patient_content)
    
    # Filter out links that don't contain "fragor-och-svar" in the URL and deduplicate by URL
    seen_urls = set()
    patient_links = []
    
    for link in links:
        if "fragor-och-svar" in link["url"] and link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            patient_links.append(link)
    
    return patient_links


def run_kry_scraper() -> Dict[str, Any]:
    """Scrapes links from kry.se/fakta and separates them by section."""
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        print("Error: JINA_API_KEY environment variable not found.")
        print(f"Ensure it is set in the .env file located at: {dotenv_path}")
        return {"success": False, "error": "API key not found"}

    reader = JinaReader(api_key)
    url = "https://www.kry.se/fakta/"
    
    print(f"\n--- Processing URL: {url} ---")
    results = reader.read_url(url)

    if not results or 'text' not in results or not results['text']:
        print(f"Failed to get valid content from URL: {url}")
        return {"success": False, "error": "Failed to get content"}

    content = results['text']
    print(f"Successfully fetched content (length: {len(content)} chars).")

    # Extract links for each section
    print("\nExtracting Fakta och råd links...")
    fakta_links = extract_fakta_och_rad_links(content)
    print(f"Found {len(fakta_links)} links in Fakta och råd section.")

    print("\nExtracting Vanliga patientfrågor links...")
    patient_links = extract_vanliga_patientfragor_links(content)
    print(f"Found {len(patient_links)} links in Vanliga patientfrågor section.")

    # Save the links to separate files
    script_dir = os.path.dirname(__file__)
    fakta_output_file = os.path.join(script_dir, "extracted_links4.txt")
    patient_output_file = os.path.join(script_dir, "extracted_links3.txt")
    
    save_links_to_file(fakta_links, fakta_output_file)
    save_links_to_file(patient_links, patient_output_file)

    return {
        "success": True,
        "fakta_links_count": len(fakta_links),
        "patient_links_count": len(patient_links)
    }

if __name__ == "__main__":
    print("Starting Kry.se link scraper...")
    print(f"Looking for .env file at: {dotenv_path}")
    
    result = run_kry_scraper()

    if result["success"]:
        print(f"\nSuccessfully extracted:")
        print(f"- {result['fakta_links_count']} links from Fakta och råd section (saved to extracted_links4.txt)")
        print(f"- {result['patient_links_count']} links from Vanliga patientfrågor section (saved to extracted_links3.txt)")
    else:
        print(f"\nScraping failed. Error: {result.get('error', 'Unknown error')}") 