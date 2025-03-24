#!/usr/bin/env python3
import os
import sys
import json
import yaml
import mimetypes
import argparse
from pathlib import Path
import base64
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

"""
Example YAML configuration file for Azure OpenAI settings:

# config.yaml
azure_openai:
  endpoint: "https://your-resource.openai.azure.com/"
  api_version: "2023-12-01-preview"
  deployment_name: "your-vision-model-deployment"
"""


def load_config(config_path):
    """Load YAML configuration file"""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Verify that required settings are present
        if "azure_openai" not in config:
            print("Error: Missing 'azure_openai' section in configuration")
            sys.exit(1)

        openai_config = config["azure_openai"]

        if "endpoint" not in openai_config:
            print(
                "Error: Missing required configuration 'endpoint' in azure_openai section"
            )
            sys.exit(1)

        if "deployment_name" not in openai_config:
            print(
                "Error: Missing required configuration 'deployment_name' in azure_openai section"
            )
            sys.exit(1)

        return config
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        sys.exit(1)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process markdown files and images in a folder and output to JSON"
    )
    parser.add_argument(
        "--input-folder",
        required=True,
        help="Path to the folder containing markdown files and images to process",
    )
    parser.add_argument(
        "--output", required=True, help="Path to save the output JSON file"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file with Azure OpenAI settings",
    )

    # Parse arguments
    args = parser.parse_args()

    # Load configuration from file
    config = load_config(args.config)

    # Get Azure OpenAI settings from config
    openai_config = config["azure_openai"]

    # Set default API version if not provided
    if "api_version" not in openai_config:
        openai_config["api_version"] = "2023-12-01-preview"

    folder_path = args.input_folder
    output_path = args.output
    root_path = Path(folder_path)

    if not root_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)

    # Get Azure credentials using DefaultAzureCredential
    try:
        # DefaultAzureCredential tries multiple authentication methods
        credential = DefaultAzureCredential()
        # Convert to token provider for OpenAI SDK
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )

        # Initialize Azure OpenAI client with token provider
        client = AzureOpenAI(
            azure_endpoint=openai_config["endpoint"],
            api_version=openai_config["api_version"],
            azure_ad_token_provider=token_provider,
        )
    except Exception as e:
        print(f"Error setting up Azure credentials: {e}")
        print("Make sure you're logged in to Azure and have the required permissions")
        sys.exit(1)

    # Initialize result list
    result = []

    # Process all files in the folder and subfolders
    for file_path in root_path.glob("**/*"):
        if file_path.is_file():
            # Get relative path
            rel_path = str(file_path.relative_to(root_path))

            # Determine file type
            mime_type, _ = mimetypes.guess_type(file_path)

            # Process file according to its type
            if mime_type and mime_type.startswith("image/"):
                # Process image file
                try:
                    print(f"Processing image: {rel_path}")

                    # Get image description from Azure OpenAI
                    with open(file_path, "rb") as image_file:
                        image_data = image_file.read()

                    # Create a base64 version for API
                    base64_image = base64.b64encode(image_data).decode("utf-8")

                    # Call Azure OpenAI API
                    response = client.chat.completions.create(
                        model=openai_config["deployment_name"],
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Describe this image in detail. Format your response in markdown.",
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                        max_tokens=5000,
                    )

                    # Extract the description
                    image_description = response.choices[0].message.content

                    result.append(
                        {
                            "filePath": rel_path,
                            "imageAltTextDescription": image_description,
                            "mimeType": mime_type,
                        }
                    )
                except Exception as e:
                    print(f"Error processing image {file_path}: {e}")

            elif file_path.suffix.lower() == ".md":
                # Process markdown file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()

                    result.append(
                        {
                            "filePath": rel_path,
                            "contents": file_content,
                            "mimeType": "text/markdown",
                        }
                    )
                except Exception as e:
                    print(f"Error processing markdown {file_path}: {e}")

    # Create output file with minimized JSON
    try:
        # Ensure the output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, separators=(",", ":"), ensure_ascii=False)

        print(f"Processing complete. Output saved to {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
