import os

# Define the target directory relative to the workspace root
target_dir = "web_scraping/cleaned_markdown_documents"

# Get the absolute path based on the workspace root
workspace_root = "/Users/olivergroth/Documents/GitHub/poc-1177" # Adjust if your workspace root is different
target_dir_abs = os.path.join(workspace_root, target_dir)

# Iterate through each file in the target directory
print(f"Processing files in: {target_dir_abs}")
for filename in os.listdir(target_dir_abs):
    # Check if it's a file and has a .md extension
    if os.path.isfile(os.path.join(target_dir_abs, filename)) and filename.endswith(".md"):
        file_path = os.path.join(target_dir_abs, filename)

        print(f"Processing {filename}...")

        try:
            # Read all lines from the file
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Check if the file has at least 3 lines
            if len(lines) >= 3:
                # Check if the third line already ends with a newline and the fourth doesn't start with one
                # Or if there's already a blank line (just '\n') as the fourth line
                if len(lines) > 3 and lines[3] == '\n':
                     print("  -> Newline already exists after line 3. Skipping.")
                     continue # Skip if already a blank line

                # Insert a newline after the third line (index 2)
                lines.insert(3, '\n')

                # Write the modified lines back to the file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                print(f"  -> Successfully added newline after line 3 in {filename}")
            else:
                print(f"  -> Skipping {filename}: File has less than 3 lines.")

        except Exception as e:
            print(f"  -> Error processing file {filename}: {e}")

print("Script finished.")