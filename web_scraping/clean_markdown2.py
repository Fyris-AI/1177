import os
import glob
import re
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional

# --- Configuration ---
SOURCE_DIR_NAME = "markdown_documents2"
DEST_DIR_NAME = "cleaned_markdown_documents2"
LINKS_FILE_NAME = "extracted_links2.txt"

# Markers for content extraction
# Start content after the line containing this marker (usually the H1 title follows)
START_MARKER_CONTAINS = "Du är här:"
# End content before the line containing this marker
END_MARKER_CONTAINS = "[Till toppen av sidan]"
# --- End Configuration ---

def extract_filename_from_url(url: str) -> str:
    """
    Extract filename from URL, making it filesystem-safe.
    Mirrors the logic used in content_scraper2.py.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.rstrip('/')
        last_part = path.split('/')[-1]
        # Handle potential empty last part if URL ends with /
        if not last_part and len(path.split('/')) > 1:
            last_part = path.split('/')[-2]

        # Basic sanitization: replace non-alphanumeric with hyphens
        safe_chars = re.sub(r'[^a-zA-Z0-9_.-]', '-', last_part)
        filename = safe_chars[:100] # Limit length

        # Ensure it has an extension and is not empty
        if not filename:
            filename = "index"
        if not filename.endswith('.md'):
            filename += ".md"

        return filename
    except Exception:
        # Fallback, though should ideally match scraper logic perfectly
        return f"file-{hash(url)}.md"

def load_url_map(links_file_path: str) -> Dict[str, str]:
    """Loads the links file and creates a mapping from filename to URL."""
    url_map = {}
    try:
        with open(links_file_path, 'r', encoding='utf-8') as f:
            next(f) # Skip header line 1
            next(f) # Skip header line 2 (blank)
            for line in f:
                match = re.match(r'\d+\.\s+\[.*?\]:\s+(https?://[^\s]+)', line)
                if match:
                    url = match.group(1).strip()
                    filename = extract_filename_from_url(url)
                    if filename not in url_map: # Keep the first URL found for a filename
                        url_map[filename] = url
                    else:
                         print(f"Warning: Duplicate filename '{filename}' generated for URL '{url}'. Keeping first URL '{url_map[filename]}'.")
    except FileNotFoundError:
        print(f"Error: Links file not found at {links_file_path}")
    except Exception as e:
        print(f"Error reading links file {links_file_path}: {e}")
    return url_map

def extract_title(lines: List[str]) -> Optional[str]:
    """Attempts to extract the title from the first few lines."""
    for line in lines[:5]: # Check first 5 lines
        stripped_line = line.strip()
        # Common pattern from Jina seems to be Title - 1177 or similar
        if stripped_line and not stripped_line.startswith('[') and not stripped_line.startswith('*'):
             # Basic check if it might be a title (not markdown link/list)
             # Further refinement might be needed based on observed patterns
            # Remove potential markdown heading markers for cleaner title
             if stripped_line.startswith('# '):
                 return stripped_line[2:].strip()
             # Remove trailing " - 1177" if present
             if " - 1177" in stripped_line:
                 return stripped_line.split(" - 1177")[0].strip()
             return stripped_line # Return the first non-empty, non-link/list line
    return None # Title not found

def clean_file(input_path: Path, output_path: Path, url_map: Dict[str, str]):
    """
    Cleans a single markdown file: removes header/footer, adds metadata header.
    """
    file_name = input_path.name
    source_url = url_map.get(file_name)

    if not source_url:
        print(f"Warning: Could not find source URL for '{file_name}'. Skipping.")
        return

    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        title = extract_title(lines)
        if not title:
            print(f"Warning: Could not extract title for '{file_name}'. Using filename as title.")
            title = file_name.replace('.md', '')

        # Find content boundaries
        start_line_index = -1
        end_line_index = len(lines)

        for i, line in enumerate(lines):
            if START_MARKER_CONTAINS in line:
                # Potential start is the line *after* the marker line,
                # preferably the first H1 after it.
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('# '):
                         start_line_index = j
                         break
                    elif lines[j].strip(): # Or the first non-empty line if no H1 found soon
                        start_line_index = j
                        break
                if start_line_index != -1:
                    break # Found start marker, stop searching

        # Fallback if START_MARKER_CONTAINS not found (maybe first H1?)
        if start_line_index == -1:
            for i, line in enumerate(lines):
                 if line.strip().startswith('# '):
                     start_line_index = i
                     print(f"Warning: '{START_MARKER_CONTAINS}' not found in '{file_name}'. Using first H1 as start.")
                     break
            if start_line_index == -1: # Still not found? Use line after title attempt
                 title_idx = -1
                 for i, line in enumerate(lines):
                     if title in line: # Find the line where the extracted title is
                         title_idx = i
                         break
                 if title_idx != -1:
                    start_line_index = title_idx + 1
                    print(f"Warning: Could not find H1 start in '{file_name}'. Starting after extracted title line.")
                 else:
                     print(f"Error: Cannot determine content start for '{file_name}'. Skipping.")
                     return # Give up if no start found

        # Find end marker
        for i in range(len(lines) - 1, start_line_index -1, -1):
            if END_MARKER_CONTAINS in lines[i]:
                end_line_index = i
                break
        # Alternative end marker if first is not found
        if end_line_index == len(lines):
             for i in range(len(lines) - 1, start_line_index -1, -1):
                 if "Mer på 1177.se" in lines[i]:
                     end_line_index = i
                     print(f"Note: '{END_MARKER_CONTAINS}' not found in '{file_name}'. Used 'Mer på 1177.se' as end marker.")
                     break

        # Extract content
        if start_line_index < end_line_index:
            content_to_keep = lines[start_line_index:end_line_index]
            # Remove leading/trailing whitespace lines
            while content_to_keep and not content_to_keep[0].strip():
                content_to_keep.pop(0)
            while content_to_keep and not content_to_keep[-1].strip():
                content_to_keep.pop(-1)

            if content_to_keep:
                # Construct header
                header = (
                    f"Filename: {file_name}\n"
                    f"Title: {title}\n"
                    f"URL Source: {source_url}\n\n"
                )
                # Write output
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(header)
                    outfile.writelines(content_to_keep)
                print(f"Successfully cleaned '{file_name}'")
            else:
                print(f"Cleaned '{file_name}' -> resulted in empty content after removing header/footer.")
                # Optionally write an empty file or skip writing
                # with open(output_path, 'w', encoding='utf-8') as outfile:
                #     pass
        else:
            print(f"Cleaned '{file_name}' -> resulted in empty content (start >= end index). Start={start_line_index}, End={end_line_index}")
            # Optionally write an empty file or skip writing

    except Exception as e:
        print(f"Error processing file {input_path.name}: {e}")

def main():
    """
    Main function to iterate through files and clean them.
    """
    script_dir = Path(__file__).parent
    source_dir = script_dir / SOURCE_DIR_NAME
    dest_dir = script_dir / DEST_DIR_NAME
    links_file_path = script_dir / LINKS_FILE_NAME

    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    print(f"Links file: {links_file_path}")

    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' not found.")
        return

    if not links_file_path.exists():
        print(f"Error: Links file '{links_file_path}' not found.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured destination directory exists: {dest_dir}")

    url_map = load_url_map(str(links_file_path))
    if not url_map:
        print("Could not load URL map from links file. Aborting.")
        return
    print(f"Loaded {len(url_map)} filename-URL mappings.")

    markdown_files = list(source_dir.glob("*.md"))

    if not markdown_files:
        print(f"No markdown files found in {source_dir}")
        return

    print(f"Found {len(markdown_files)} markdown files to process.")

    processed_count = 0
    for file_path in markdown_files:
        output_file_path = dest_dir / file_path.name
        clean_file(file_path, output_file_path, url_map)
        processed_count += 1

    print(f"\nFinished processing {processed_count} files.")

if __name__ == "__main__":
    main() 