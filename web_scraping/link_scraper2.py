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
    Extract all markdown links: [text](url)
    """
    links = []
    pattern = r'\[(.*?)\]\((https?://[^\s()]+)\)' # Avoid matching )) in URLs
    matches = re.findall(pattern, content)

    for text, url in matches:
        # Basic cleaning of text
        clean_text = text.strip().replace('\n', ' ').replace('\r', '')
        # Remove trailing punctuation from URL if accidentally captured
        url = url.strip().rstrip('.,;:')
        links.append({
            "text": clean_text,
            "url": url
        })

    return links

def filter_relevant_links(links: List[Dict[str, str]], mother_url: str) -> List[Dict[str, str]]:
    """Filters links to keep only those under the mother URL's path hierarchy."""
    relevant_links = []
    try:
        parsed_mother = urlparse(mother_url)
        # Ensure path ends with / for comparison, handle root path correctly
        mother_path = parsed_mother.path if parsed_mother.path.endswith('/') else parsed_mother.path + '/'
        if mother_path == '//': # Handle case where mother path is just '/'
             mother_path = '/'
    except ValueError as e:
        print(f"Error parsing mother URL '{mother_url}': {e}")
        return []

    for link in links:
        try:
            parsed_link = urlparse(link['url'])
            link_path = parsed_link.path

            # Check 1: Same domain
            if parsed_link.netloc != parsed_mother.netloc:
                continue

            # Check 2: Path starts with mother path
            if not link_path.startswith(mother_path):
                 continue

            # Check 3: Path is longer than mother path (i.e., it's a sub-page)
            # Use rstrip to handle optional trailing slashes consistently
            if len(link_path.rstrip('/')) <= len(mother_path.rstrip('/')):
                 continue

            # Check 4: Exclude URLs containing '#' (fragments) or parameters likely not content pages
            # Allow query parameters if they seem necessary (like ?id=...) - this is tricky.
            # Let's be simple first: exclude fragments. Parameters might be needed.
            if '#' in link['url']:
                 continue

            # Check 5: Exclude links ending with common non-page extensions (optional, can be refined)
            # common_non_page_extensions = ('.pdf', '.jpg', '.png', '.svg', '.aspx', '.zip', '.docx')
            # if link_path.lower().endswith(common_non_page_extensions):
            #     continue

            relevant_links.append(link)
        except ValueError as e:
            print(f"Error parsing link URL '{link.get('url')}': {e}")
            continue # Skip malformed URLs

    return relevant_links


def save_links_to_file(links: List[Dict[str, str]], output_file: str):
    """Saves the list of links to a text file, sorted alphabetically by text."""
    # Sort by link text, case-insensitive
    sorted_links = sorted(links, key=lambda x: x['text'].lower())

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Total unique relevant links found: {len(sorted_links)}\n\n")
            for i, link in enumerate(sorted_links, 1):
                 # Text is already cleaned during extraction
                 f.write(f"{i}. [{link['text']}]: {link['url']}\n")
        print(f"\nLinks saved to {output_file}")
    except IOError as e:
        print(f"Error writing to file {output_file}: {e}")


def run_multi_url_scraper(urls: List[str], output_file: str) -> Dict[str, Any]:
    """Scrapes relevant links from multiple URLs."""
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        print("Error: JINA_API_KEY environment variable not found.")
        print(f"Ensure it is set in the .env file located at: {dotenv_path}")
        return {"success": False, "error": "API key not found"}

    reader = JinaReader(api_key)
    # Use a set of tuples (text, url) for automatic deduplication based on both fields
    all_relevant_links_set: Set[Tuple[str, str]] = set()

    for url in urls:
        print(f"\n--- Processing URL: {url} ---")
        results = reader.read_url(url)

        if not results or 'text' not in results or not results['text']:
            print(f"Failed to get valid content from URL: {url}")
            continue

        content = results['text']
        print(f"Successfully fetched content (length: {len(content)} chars).")

        print(f"Extracting all links from: {url}")
        all_links_on_page = extract_links(content)
        print(f"Found {len(all_links_on_page)} total links on page.")

        print(f"Filtering relevant sub-page links for: {url}")
        relevant_links = filter_relevant_links(all_links_on_page, url)
        print(f"Found {len(relevant_links)} relevant links.")

        added_count = 0
        for link in relevant_links:
             link_tuple = (link['text'], link['url'])
             if link_tuple not in all_relevant_links_set:
                 all_relevant_links_set.add(link_tuple)
                 added_count += 1
        print(f"Added {added_count} new unique relevant links to the list.")


    # Convert set of tuples back to list of dicts for saving
    final_links_list = [{"text": text, "url": url} for text, url in all_relevant_links_set]

    if not final_links_list:
        print("\nNo relevant links found across all URLs.")
        return {"success": True, "count": 0, "message": "No relevant links found."}

    # Save the aggregated unique links
    save_links_to_file(final_links_list, output_file)

    return {
        "success": True,
        "count": len(final_links_list),
        "sample": final_links_list[0] if final_links_list else None # Sample will be based on sorted list
    }

if __name__ == "__main__":
    mother_urls = [
        "https://www.1177.se/liv--halsa/",
        "https://www.1177.se/barn--gravid/",
        "https://www.1177.se/olyckor--skador/",
        "https://www.1177.se/sjukdomar--besvar/",
        "https://www.1177.se/undersokning-behandling/",
        "https://www.1177.se/sa-fungerar-varden/"
    ]
    output_filename = "extracted_links2.txt"
    # Ensure the output file path is relative to the script's directory
    script_dir = os.path.dirname(__file__)
    output_filepath = os.path.join(script_dir, output_filename)

    print(f"Starting scraper for {len(mother_urls)} URLs...")
    print(f"Output will be saved to: {output_filepath}")
    print(f"Looking for .env file at: {dotenv_path}")

    result = run_multi_url_scraper(mother_urls, output_filepath)

    if result["success"]:
        print(f"\nSuccessfully extracted {result['count']} unique relevant links.")
        # Sample link is now the first one alphabetically by text
        if result.get('sample'):
            # Use ensure_ascii=False for correct printing of Swedish characters
            print(f"Sample link (alphabetical first): {json.dumps(result['sample'], indent=2, ensure_ascii=False)}")
    else:
        print(f"\nScraping failed. Error: {result.get('error', 'Unknown error')}") 