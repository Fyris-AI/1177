import os
import re
import time
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Tuple

import requests
from dotenv import load_dotenv

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

            # Handle response content type
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                data = response.json()
                if isinstance(data, dict) and 'data' in data and 'content' in data['data']:
                    return {"text": data['data']['content']}
                elif isinstance(data, dict) and 'content' in data:
                    return {"text": data['content']}
                else:
                    print("JSON response received, but 'content' field missing. Using raw text.")
                    return {"text": response.text}
            elif 'text/markdown' in content_type or 'text/plain' in content_type:
                print("Received text/markdown response.")
                return {"text": response.text}
            else:
                print(f"Unexpected Content-Type: {content_type}. Reading as text.")
                return {"text": response.text}

        except requests.Timeout:
            print(f"Timeout occurred while reading URL: {url}")
            return {}
        except requests.RequestException as e:
            print(f"Error reading URL {url}: {e}")
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
            return {"text": response.text}
        except Exception as e:
            print(f"An unexpected error occurred for URL {url}: {e}")
            return {}

def read_links_from_file(file_path: str) -> List[Dict[str, str]]:
    """
    Read links from the specified links file.
    Assumes format: N. [text]: url
    Skips header lines.
    """
    links = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip the first two lines (total count and empty line)
            next(f)
            next(f)

            for line in f:
                # Parse the line: "N. [text]: url"
                match = re.match(r'\d+\.\s+\[(.*?)?\]:\s+(https?://[^\s]+)', line) # Allow empty brackets
                if match:
                    text, url = match.groups()
                    links.append({
                        "text": text.strip() if text else "", # Handle empty text
                        "url": url.strip()
                    })
    except FileNotFoundError:
        print(f"Error: Links file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading links file {file_path}: {e}")
        return []

    return links

def extract_filename_from_url(url: str) -> str:
    """
    Extract filename from URL, making it filesystem-safe.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.rstrip('/')
        last_part = path.split('/')[-1]
        # Handle potential empty last part if URL ends with /
        if not last_part and len(path.split('/')) > 1:
            last_part = path.split('/')[-2]

        # Basic sanitization: replace non-alphanumeric with hyphens
        # Limit length to avoid issues on some filesystems
        safe_chars = re.sub(r'[^a-zA-Z0-9_.-]', '-', last_part)
        filename = safe_chars[:100] # Limit length

        # Ensure it has an extension and is not empty
        if not filename:
            filename = "index"
        if not filename.endswith('.md'):
             filename += ".md"

        return filename
    except Exception as e:
        print(f"Error generating filename for URL {url}: {e}. Using default.")
        # Create a fallback filename based on hash or index if needed
        return f"file-{hash(url)}.md"

def save_content_to_file(content: str, output_dir: str, filename: str) -> bool:
    """
    Save content to a markdown file in the specified directory.
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Saved content to {file_path}")
        return True
    except IOError as e:
        print(f"Error saving content to {filename}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error saving file {filename}: {e}")
        return False

def scrape_content(links: List[Dict[str, str]], output_dir: str, limit: int = None) -> List[Tuple[str, bool]]:
    """
    Scrape content from links and save to files.
    """
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        print("Error: JINA_API_KEY environment variable not found.")
        print(f"Ensure it is set in the .env file located at: {dotenv_path}")
        return []

    reader = JinaReader(api_key)
    results = []

    links_to_process = links[:limit] if limit else links
    total_links = len(links_to_process)

    for i, link in enumerate(links_to_process, 1):
        url = link["url"]
        print(f"\nProcessing link {i}/{total_links}: {url}")

        filename = extract_filename_from_url(url)

        content_data = reader.read_url(url)

        if not content_data or 'text' not in content_data or not content_data['text']:
            print(f"Failed to get valid content from {url}")
            results.append((filename, False))
            continue

        success = save_content_to_file(content_data['text'], output_dir, filename)
        results.append((filename, success))

        # Add a delay to potentially avoid rate limits
        if i < total_links:
            delay = 5 # Reduced delay slightly
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)

    return results

def main():
    """
    Main function to run the content scraper.
    """
    # Use the links file from extracted_links4.txt and a new output directory
    script_dir = os.path.dirname(__file__)
    links_filename = "extracted_links4.txt"
    output_dirname = "markdown_documents4"

    links_filepath = os.path.join(script_dir, links_filename)
    output_dirpath = os.path.join(script_dir, output_dirname)

    limit = None  # Process all links (set to a number like 5 to limit for testing)

    print(f"Starting content scraper for Kry.se patient questions...")
    print(f"Reading links from: {links_filepath}")
    print(f"Saving markdown files to: {output_dirpath}")
    print(f"Looking for .env file at: {dotenv_path}")

    all_links = read_links_from_file(links_filepath)
    if not all_links:
        print("No links found in the input file. Exiting.")
        return

    print(f"Found {len(all_links)} links to process.")

    # No filtering needed as extracted_links4.txt should contain relevant links

    links_to_scrape = all_links
    count_to_scrape = len(links_to_scrape)
    if limit:
        count_to_scrape = min(limit, len(links_to_scrape))

    print(f"Scraping content from {count_to_scrape} links...")
    results = scrape_content(links_to_scrape, output_dirpath, limit)

    # Print summary
    successes = sum(1 for _, success in results if success)
    failures = len(results) - successes
    print(f"\n--- Scraping Complete ---")
    print(f"Summary: {successes} successful, {failures} failed out of {len(results)} processed links.")

    if successes > 0:
        print("\nSuccessfully created/updated the following files:")
        # Optionally list successful files - might be too long for many files
        # for filename, success in results:
        #     if success:
        #         print(f"- {filename}")
        print(f"(List of successful files omitted for brevity if large number)")
    if failures > 0:
         print("\nFailed attempts:")
         for filename, success in results:
              if not success:
                  print(f"- Failed for link corresponding to potential file: {filename}")

if __name__ == "__main__":
    main() 