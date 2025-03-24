#!/usr/bin/env python3
import os
import sys
import json
import base64
import mimetypes
import argparse
from pathlib import Path

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Process markdown files and images in a folder and output to JSON'
    )
    parser.add_argument(
        '--input-folder',
        required=True,
        help='Path to the folder containing markdown files and images to process'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to save the output JSON file'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    folder_path = args.input_folder
    output_path = args.output
    root_path = Path(folder_path)
    
    if not root_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    # Initialize result list
    result = []
    
    # Process all files in the folder and subfolders
    for file_path in root_path.glob('**/*'):
        if file_path.is_file():
            # Get relative path
            rel_path = str(file_path.relative_to(root_path))
            
            # Determine file type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Process file according to its type
            if mime_type and mime_type.startswith('image/'):
                # Process image file
                try:
                    with open(file_path, 'rb') as f:
                        file_content = base64.b64encode(f.read()).decode('utf-8')
                    
                    result.append({
                        "filePath": rel_path,
                        "contents": file_content,
                        "mimeType": mime_type,
                        "isBase64Encoded": True
                    })
                except Exception as e:
                    print(f"Error processing image {file_path}: {e}")
            
            elif file_path.suffix.lower() == '.md':
                # Process markdown file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    result.append({
                        "filePath": rel_path,
                        "contents": file_content,
                        "mimeType": "text/markdown",
                        "isBase64Encoded": False
                    })
                except Exception as e:
                    print(f"Error processing markdown {file_path}: {e}")
    
    # Create output file with minimized JSON
    try:
        # Ensure the output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, separators=(',', ':'), ensure_ascii=False)
        
        print(f"Processing complete. Output saved to {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()