import os

# Define the target directory relative to the workspace root
data_dir = "backend/data"
workspace_root = "/Users/olivergroth/Documents/GitHub/poc-1177" # Adjust if your workspace root is different
full_data_dir_path = os.path.join(workspace_root, data_dir)

# Check if the directory exists
if not os.path.isdir(full_data_dir_path):
    print(f"Error: Directory not found at {full_data_dir_path}")
    exit(1)

print(f"Processing files in: {full_data_dir_path}")

# Iterate over all entries in the directory
for filename in os.listdir(full_data_dir_path):
    file_path = os.path.join(full_data_dir_path, filename)

    # Ensure it's a file and not a directory
    if os.path.isfile(file_path):
        print(f"Processing file: {filename}")
        try:
            # Read the original content
            # Use utf-8 encoding, common for text files
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Prepare the header line
            header = f"Filename: {filename}\n\n" # Adds filename and two newlines

            # Write the header and the original content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(original_content)

            print(f"Successfully added header to: {filename}")

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

print("\nScript finished.") 