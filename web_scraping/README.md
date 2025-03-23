# Jina AI Web Scraper

This project uses Jina AI to scrape links and content from medical knowledge websites and save them as markdown files.

## Setup

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure your `.env` file contains your Jina API key:
   ```
   JINA_API_KEY=your_jina_api_key_here
   ```

## Link Scraper

The `link_scraper.py` script scrapes all links from a website and saves them to a text file.

### Usage

Run the script with the default URL (https://vardpersonal.1177.se/kunskapsstod/):

```
python link_scraper.py
```

The script will:
1. Connect to the URL using Jina AI Reader API
2. Extract all links from the page
3. Save the links to `extracted_links.txt` in the current directory

## Content Scraper

The `content_scraper.py` script reads links from `extracted_links.txt` and scrapes the content of each link, saving it as a markdown file.

### Usage

Run the script to scrape content from the first 5 links:

```
python content_scraper.py
```

The script will:
1. Read links from `extracted_links.txt`
2. Filter out anchor links and focus on content links
3. Scrape content from the first 5 content links
4. Save each page's content to a markdown file in the `markdown_documents` directory
5. Use the end of the URL path as the filename (e.g., `adhd.md`)

### Customization

To scrape more or different links, edit the following variables in the script:

```python
# In content_scraper.py
limit = 5  # Change this number to scrape more links (or set to None for all links)
```

```python
# In link_scraper.py
url = "https://your-url-here.com"  # Change this to scrape a different site
output_file = "your-output-file.txt"  # Change the output filename
``` 