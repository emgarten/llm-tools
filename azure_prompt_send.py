#!/usr/bin/env python3
import argparse
import sys
import yaml
import time
from openai import AzureOpenAI
from azure.identity import AzureCliCredential, DefaultAzureCredential, get_bearer_token_provider

"""
Azure OpenAI API Requester

A script to send requests to Azure OpenAI and save the responses using Azure SDK credentials.

Example config.yaml:
---
azure_openai:
  endpoint: "https://your-resource.openai.azure.com/"
  api_version: "2023-12-01-preview"
  deployment_name: "your-model-deployment"
  max_completion_tokens: 2000
  reasoning_effort: "high"
"""

_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"

def load_config(config_path):
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def load_prompt(prompt_path, additional_path=None):
    """Load prompt from file and optionally append additional content."""
    try:
        with open(prompt_path, "r") as file:
            prompt = file.read()

        if additional_path:
            print(f"Adding additional content from {additional_path}")
            with open(additional_path, "r") as file:
                additional_content = file.read()
            prompt = f"{prompt}\n\n{additional_content}"

        return prompt
    except Exception as e:
        print(f"Error loading prompt: {e}")
        sys.exit(1)


def save_response(response_text, output_path):
    """Save response to specified output file."""
    try:
        with open(output_path, "w") as file:
            file.write(response_text)
        print(f"Response saved to {output_path}")
    except Exception as e:
        print(f"Error saving response: {e}")
        sys.exit(1)

def get_token_provider():
    """Get Azure credentials using the Azure SDK."""
    try:
        print("Getting Azure credentials using AzureCliCredential...")


        try:
            credential = AzureCliCredential()
            credential.get_token(_OPENAI_SCOPE)
            return get_bearer_token_provider(credential, _OPENAI_SCOPE)
        except Exception as cli_error:
            credential = DefaultAzureCredential()
            credential.get_token(_OPENAI_SCOPE)
            return get_bearer_token_provider(credential, _OPENAI_SCOPE)

    except Exception as e:
        print(f"Error getting Azure credentials: {e}")
        print(
            "Please ensure you are logged in to Azure. Run 'az login' in your terminal."
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Send requests to Azure OpenAI API using Azure SDK credentials"
    )
    parser.add_argument("--config", required=True, help="Path to config YAML file")
    parser.add_argument("--prompt", required=True, help="Path to prompt text file")
    parser.add_argument(
        "--additional", help="Path to additional content to append to prompt"
    )
    parser.add_argument("--output", required=True, help="Path to save the response")
    args = parser.parse_args()

    # Load configuration
    print(f"Loading configuration from {args.config}")
    config = load_config(args.config)
    azure_config = config.get("azure_openai", {})

    # Validate required configs
    required_keys = ["endpoint", "api_version", "deployment_name"]
    missing_keys = [key for key in required_keys if key not in azure_config]
    if missing_keys:
        print(f"Missing required configuration keys: {', '.join(missing_keys)}")
        sys.exit(1)

    # Get max tokens and reasoning level from config
    max_completion_tokens = azure_config.get(
        "max_completion_tokens", 10000
    )  # Default if not specified
    reasoning_effort = azure_config.get(
        "reasoning_effort", "medium"
    )  # Default if not specified

    # Load prompt
    prompt_text = load_prompt(args.prompt, args.additional)

    # Set up Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=azure_config["endpoint"],
        api_version=azure_config["api_version"],
        azure_ad_token_provider=get_token_provider(),
    )

    # Send request
    print(
        f"Sending request to Azure OpenAI deployment '{azure_config['deployment_name']}'"
    )
    print(
        f"Using max_completion_tokens: {max_completion_tokens} and reasoning_effort: {reasoning_effort}"
    )

    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=azure_config["deployment_name"],
            messages=[
                {"role": "user", "content": prompt_text},
            ],
            max_completion_tokens=max_completion_tokens,
            extra_body={"reasoning_effort": reasoning_effort},
        )

        # Extract response text
        response_text = response.choices[0].message.content

        # Print usage information
        print("\nUsage Information:")
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Completion tokens: {response.usage.completion_tokens}")
        print(f"Total tokens: {response.usage.total_tokens}")

        # Save response
        save_response(response_text, args.output)

        elapsed_time = time.time() - start_time
        print(f"Request completed in {elapsed_time:.2f} seconds")

    except Exception as e:
        print(f"Error during API request: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
