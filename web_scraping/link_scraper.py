import os
import re
import json
import requests
from typing import Dict, Any, List
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

def extract_links(content: str) -> List[Dict[str, str]]:
    """
    Extract links from markdown content
    
    Args:
        content: Markdown content as string
        
    Returns:
        List of dictionaries with link text and URL
    """
    # Regular expression to find markdown links: [text](url)
    links = []
    
    # Match markdown links pattern
    pattern = r'\[(.*?)\]\((https?://[^\s)]+)\)'
    matches = re.findall(pattern, content)
    
    for text, url in matches:
        links.append({
            "text": text.strip(),
            "url": url.strip()
        })
    
    return links

def save_links_to_file(links: List[Dict[str, str]], output_file: str):
    """
    Save links to a text file
    
    Args:
        links: List of dictionaries with link text and URL
        output_file: Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Total links found: {len(links)}\n\n")
        
        for i, link in enumerate(links, 1):
            f.write(f"{i}. [{link['text']}]: {link['url']}\n")
    
    print(f"Links saved to {output_file}")

def run_link_scraper(url: str, output_file: str) -> Dict[str, Any]:
    """
    Run the link scraper for a given URL
    
    Args:
        url: URL to scrape for links
        output_file: Path to the output file
        
    Returns:
        Dictionary with scraping results
    """
    api_key = os.getenv("JINA_API_KEY")
    
    if not api_key:
        print("JINA_API_KEY environment variable not found")
        return {"success": False, "error": "API key not found"}
    
    # Get content from API
    print(f"Fetching content from URL: {url}")
    reader = JinaReader(api_key)
    results = reader.read_url(url)
    
    if not results or 'text' not in results:
        print("Failed to get content from URL or no text content found")
        return {"success": False, "error": "Failed to get content"}
    
    # Extract links
    print("Extracting links...")
    links = extract_links(results['text'])
    
    # Print link count
    print(f"Found {len(links)} links.")
    
    if not links:
        return {"success": False, "error": "No links found", "count": 0}
    
    # Save links to file
    save_links_to_file(links, output_file)
    
    return {
        "success": True,
        "count": len(links),
        "sample": links[0] if links else None
    }

if __name__ == "__main__":
    url = "https://vardpersonal.1177.se/kunskapsstod/"
    output_file = "extracted_links.txt"
    
    result = run_link_scraper(url, output_file)
    
    if result["success"]:
        print(f"Successfully extracted {result['count']} links")
        print(f"Sample link: {json.dumps(result['sample'], indent=2)}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}") 