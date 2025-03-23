import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Tuple

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JinaReader:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            self.headers["Content-Type"] = "application/json"

    def read_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL using Jina Reader API
        """
        try:
            # The correct way to use Jina Reader is to prepend r.jina.ai/ to the URL
            reader_url = f"https://r.jina.ai/{url}"
            print(f"Making request to: {reader_url}")
            
            response = requests.get(
                reader_url,
                headers=self.headers
            )
            print(f"Status code: {response.status_code}")
            
            response.raise_for_status()
            
            # If the response is text/markdown or text/plain, return as {"text": content}
            content_type = response.headers.get('Content-Type', '')
            if 'text/markdown' in content_type or 'text/plain' in content_type:
                return {"text": response.text}
            else:
                return response.json()
        except requests.RequestException as e:
            print(f"Error reading URL: {e}")
            return {}

def read_links_from_file(file_path: str) -> List[Dict[str, str]]:
    """
    Read links from the extracted_links.txt file
    
    Args:
        file_path: Path to the file containing links
        
    Returns:
        List of dictionaries with link text and URL
    """
    links = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip the first two lines (total count and empty line)
        next(f)
        next(f)
        
        for line in f:
            # Parse the line: "N. [text]: url"
            match = re.match(r'\d+\.\s+\[(.*?)\]:\s+(https?://[^\s]+)', line)
            if match:
                text, url = match.groups()
                links.append({
                    "text": text.strip(),
                    "url": url.strip()
                })
    
    return links

def extract_filename_from_url(url: str) -> str:
    """
    Extract filename from URL
    
    Args:
        url: URL to extract filename from
        
    Returns:
        Filename based on the end of the URL path
    """
    # Parse the URL
    parsed_url = urllib.parse.urlparse(url)
    
    # Get the path and remove trailing slash if present
    path = parsed_url.path.rstrip('/')
    
    # Extract the last part of the path
    last_part = path.split('/')[-1]
    
    # Replace any non-alphanumeric characters with hyphens
    cleaned_filename = re.sub(r'[^a-zA-Z0-9]', '-', last_part)
    
    return f"{cleaned_filename}.md"

def save_content_to_file(content: str, output_dir: str, filename: str) -> bool:
    """
    Save content to a markdown file
    
    Args:
        content: Content to save
        output_dir: Directory to save the file in
        filename: Filename to use
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create full path
        file_path = os.path.join(output_dir, filename)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved content to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving content to {filename}: {e}")
        return False

def filter_content_links(links: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter links to get only content links (not anchor links)
    
    Args:
        links: List of dictionaries with link text and URL
        
    Returns:
        Filtered list of dictionaries with content links
    """
    content_links = []
    
    for link in links:
        url = link["url"]
        
        # Skip anchor links (links with # in them)
        if '#' in url:
            continue
            
        # Look for links to actual content pages
        if 'kliniska-kunskapsstod' in url or 'vardprogram' in url or 'vardriktlinjer' in url or 'vardforlopp' in url:
            content_links.append(link)
    
    return content_links

def scrape_content(links: List[Dict[str, str]], output_dir: str, limit: int = None) -> List[Tuple[str, bool]]:
    """
    Scrape content from links and save to files
    
    Args:
        links: List of dictionaries with link text and URL
        output_dir: Directory to save the files in
        limit: Maximum number of links to scrape (None for all)
        
    Returns:
        List of tuples with filename and success status
    """
    api_key = os.getenv("JINA_API_KEY")
    
    if not api_key:
        print("JINA_API_KEY environment variable not found")
        return []
    
    reader = JinaReader(api_key)
    results = []
    
    # Limit the number of links if requested
    if limit:
        links = links[:limit]
    
    for i, link in enumerate(links, 1):
        url = link["url"]
        print(f"\nProcessing link {i}/{len(links)}: {url}")
        
        # Extract filename from URL
        filename = extract_filename_from_url(url)
        
        # Scrape content
        content = reader.read_url(url)
        
        if not content or 'text' not in content:
            print(f"Failed to get content from {url}")
            results.append((filename, False))
            continue
        
        # Save content to file
        success = save_content_to_file(content['text'], output_dir, filename)
        results.append((filename, success))
        
        # Add a delay to avoid hitting rate limits
        if i < len(links):
            print("Waiting 10 seconds before next request...")
            time.sleep(10)
    
    return results

def main():
    """
    Main function
    """
    links_file = "extracted_links.txt"
    output_dir = "markdown_documents"
    limit = None  # Process all links
    
    # Read links from file
    print(f"Reading links from {links_file}...")
    all_links = read_links_from_file(links_file)
    print(f"Found {len(all_links)} links in the file")
    
    # Filter for content links
    content_links = filter_content_links(all_links)
    print(f"Filtered to {len(content_links)} content links")
    
    # Scrape content and save to files
    if limit is None:
        print(f"Scraping content from all {len(content_links)} links...")
    else:
        print(f"Scraping content from {min(limit, len(content_links))} links...")
    results = scrape_content(content_links, output_dir, limit)
    
    # Print summary
    successes = sum(1 for _, success in results if success)
    failures = sum(1 for _, success in results if not success)
    print(f"\nSummary: {successes} successful, {failures} failed")
    
    # Print filenames of successful scrapes
    if successes > 0:
        print("\nSuccessfully created the following files:")
        for filename, success in results:
            if success:
                print(f"- {filename}")

if __name__ == "__main__":
    main() 