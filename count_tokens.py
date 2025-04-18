import os
import tiktoken

# Define the target directory relative to the workspace root
target_dir = "web_scraping/cleaned_markdown_documents"

# Get the absolute path based on the workspace root
workspace_root = "/Users/olivergroth/Documents/GitHub/poc-1177" # Adjust if your workspace root is different
target_dir_abs = os.path.join(workspace_root, target_dir)

# Initialize total token count
total_tokens = 0
file_count = 0

# Specify the encoding model (cl100k_base is common for gpt-4, gpt-3.5-turbo, text-embedding-ada-002)
try:
    encoding = tiktoken.get_encoding("cl100k_base")
    print("Using tiktoken encoding: cl100k_base")
except Exception as e:
    print(f"Error getting tiktoken encoding: {e}")
    print("Please ensure tiktoken is installed correctly (`pip install tiktoken`)")
    exit()


# Iterate through each file in the target directory
print(f"\nCalculating tokens in: {target_dir_abs}")
for filename in os.listdir(target_dir_abs):
    # Check if it's a file and has a .md extension
    if os.path.isfile(os.path.join(target_dir_abs, filename)) and filename.endswith(".md"):
        file_path = os.path.join(target_dir_abs, filename)
        file_count += 1

        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Encode the content and count tokens
            tokens = encoding.encode(content)
            num_tokens = len(tokens)
            total_tokens += num_tokens

            # Optional: Print token count for each file
            # print(f"  - {filename}: {num_tokens} tokens")

        except Exception as e:
            print(f"  -> Error processing file {filename}: {e}")

# Print the total token count
print(f"\nProcessed {file_count} markdown files.")
print(f"Total token count for all documents: {total_tokens}")
