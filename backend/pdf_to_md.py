from pathlib import Path
import PyPDF2
import os

def convert_pdf_to_md(pdf_path: str, output_dir: str) -> str:
    """
    Convert a PDF file to markdown format.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the markdown file
        
    Returns:
        Path to the created markdown file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base filename without extension
    base_name = Path(pdf_path).stem
    md_path = os.path.join(output_dir, f"{base_name}.md")
    
    try:
        # Open and read the PDF
        with open(pdf_path, 'rb') as file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            markdown_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                # Basic formatting
                # Replace multiple newlines with double newlines for markdown paragraphs
                text = text.replace('\n\n\n', '\n\n')
                # Add page number as header
                markdown_content.append(f"## Page {page_num + 1}\n\n{text}\n")
            
            # Write to markdown file
            with open(md_path, 'w', encoding='utf-8') as md_file:
                md_file.write('\n'.join(markdown_content))
            
            print(f"Successfully converted {pdf_path} to {md_path}")
            return md_path
            
    except Exception as e:
        print(f"Error converting {pdf_path}: {str(e)}")
        return None

def process_pdf_directory(pdf_dir: str, output_dir: str) -> list:
    """
    Process all PDF files in a directory and convert them to markdown.
    
    Args:
        pdf_dir: Directory containing PDF files
        output_dir: Directory to save markdown files
        
    Returns:
        List of paths to created markdown files
    """
    converted_files = []
    
    # Get all PDF files in the directory
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        md_path = convert_pdf_to_md(pdf_path, output_dir)
        if md_path:
            converted_files.append(md_path)
    
    return converted_files

if __name__ == "__main__":
    # Define paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.join(current_dir, "data", "pdf")
    output_dir = os.path.join(current_dir, "data", "markdown")
    
    # Process all PDFs
    converted_files = process_pdf_directory(pdf_dir, output_dir)
    
    print(f"\nConversion complete. Converted {len(converted_files)} files:")
    for file in converted_files:
        print(f"- {file}") 