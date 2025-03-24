#!/usr/bin/env python3
import sys
import tiktoken
import argparse


def count_tokens(file_path):
    """
    Count the number of tokens in a text file using different tokenizers.

    Args:
        file_path (str): Path to the text file

    Returns:
        dict: Dictionary with model names and their token counts
    """
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Get encodings for different models
        gpt4o_encoding = tiktoken.encoding_for_model("gpt-4o")
        claude_encoding = tiktoken.get_encoding("cl100k_base")

        # Count tokens for each model
        gpt4o_tokens = len(gpt4o_encoding.encode(text))
        claude_tokens = len(claude_encoding.encode(text))

        return {"gpt-4o": gpt4o_tokens, "cl100k_base (Claude)": claude_tokens}
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Count tokens in a text file for different LLM models."
    )
    parser.add_argument("file_path", help="Path to the text file")

    # Parse arguments
    args = parser.parse_args()

    # Count tokens for different models
    token_counts = count_tokens(args.file_path)

    # Print results
    print(f"Token counts for file: {args.file_path}")
    print("-" * 40)
    for model, count in token_counts.items():
        print(f"{model}: {count} tokens")


if __name__ == "__main__":
    main()
