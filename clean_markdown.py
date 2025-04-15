import os
import glob

SOURCE_DIR = "/Users/buyn/Desktop/poc-1177/web_scraping/markdown_documents"
DEST_DIR = "/Users/buyn/Desktop/poc-1177/web_scraping/cleaned_markdown_documents"
MD_CONTENT_MARKER = "Markdown Content:"
SIDANS_MARKER = "Sidans innehåll"

def clean_file(input_path, output_path):
    """
    Cleans markdown files based on marker occurrences.
    - If >= 2 'Sidans innehåll': Keep content between first and last.
    - If == 1 'Sidans innehåll': Keep content between 'Markdown Content:' and the single marker.
    - If == 0 'Sidans innehåll': Keep content after 'Markdown Content:' to EOF.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        marker_indices = [i for i, line in enumerate(lines) if SIDANS_MARKER in line]
        md_content_index = -1
        for i, line in enumerate(lines):
            if MD_CONTENT_MARKER in line:
                md_content_index = i
                break

        slice_start = -1
        slice_end = -1
        status = ""

        if len(marker_indices) >= 2:
            # Case A: >= 2 markers - Use first and last
            slice_start = marker_indices[0] + 1
            slice_end = marker_indices[-1]
            status = f"kept lines {slice_start + 1}-{slice_end} (between first/last '{SIDANS_MARKER}')"
        elif len(marker_indices) == 1:
            # Case B: == 1 marker - Use MD_CONTENT_MARKER and the single marker
            if md_content_index != -1:
                slice_start = md_content_index + 1
                slice_end = marker_indices[0]
                status = f"kept lines {slice_start + 1}-{slice_end} (between '{MD_CONTENT_MARKER}' and single '{SIDANS_MARKER}')"
            else:
                print(f"Warning: Single '{SIDANS_MARKER}' found but no '{MD_CONTENT_MARKER}' in '{os.path.basename(input_path)}'. Skipping file.")
                return
        else: # len(marker_indices) == 0
            # Case C: == 0 markers - Use MD_CONTENT_MARKER to EOF
            if md_content_index != -1:
                slice_start = md_content_index + 1
                slice_end = len(lines)
                status = f"kept lines {slice_start + 1}-EOF (no '{SIDANS_MARKER}', used '{MD_CONTENT_MARKER}')"
            else:
                print(f"Warning: No '{SIDANS_MARKER}' or '{MD_CONTENT_MARKER}' found in '{os.path.basename(input_path)}'. Skipping file.")
                return

        # --- Extraction and Writing --- 
        if slice_start != -1 and slice_end != -1 and slice_start < slice_end:
            content_to_keep = lines[slice_start : slice_end]
            # Remove leading/trailing empty lines 
            while content_to_keep and content_to_keep[0].strip() == "":
                content_to_keep.pop(0)
            while content_to_keep and content_to_keep[-1].strip() == "":
                content_to_keep.pop(-1)

            if content_to_keep:
                 print(f"Successfully cleaned '{os.path.basename(input_path)}' -> {status}")
                 with open(output_path, 'w', encoding='utf-8') as outfile:
                     outfile.writelines(content_to_keep)
            else:
                 print(f"Cleaned '{os.path.basename(input_path)}' -> Empty output (no content between markers or only whitespace)")
                 with open(output_path, 'w', encoding='utf-8') as outfile:
                    pass # Write empty file
        else:
            # This case includes slice_start >= slice_end
            print(f"Cleaned '{os.path.basename(input_path)}' -> Empty output (start marker was at or after end marker based on detected type)")
            with open(output_path, 'w', encoding='utf-8') as outfile:
                pass # Write empty file

    except Exception as e:
        print(f"Error processing file {input_path}: {e}")

def main():
    """
    Main function to iterate through files and clean them.
    """
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created destination directory: {DEST_DIR}")

    markdown_files = glob.glob(os.path.join(SOURCE_DIR, "*.md"))

    if not markdown_files:
        print(f"No markdown files found in {SOURCE_DIR}")
        return

    print(f"Found {len(markdown_files)} markdown files to process.")

    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        output_file_path = os.path.join(DEST_DIR, file_name)
        clean_file(file_path, output_file_path)

    print("Finished processing all files.")

if __name__ == "__main__":
    main() 