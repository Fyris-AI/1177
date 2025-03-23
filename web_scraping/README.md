# Jina AI Web Scraper

This script uses Jina AI to scrape links from websites and save them to a text file.

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

## Usage

Run the script with the default URL (https://vardpersonal.1177.se/kunskapsstod/):

```
python link_scraper.py
```

The script will:
1. Connect to the URL using Jina AI Reader API
2. Extract all links from the page
3. Save the links to `extracted_links.txt` in the current directory

## Customization

To scrape a different URL or change the output file, edit the variables at the bottom of the script:

```python
url = "https://your-url-here.com"
output_file = "your-output-file.txt"
``` 