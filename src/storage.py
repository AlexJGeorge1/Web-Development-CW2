"""
Storage module: saves and loads the inverted index to/from a JSON file.

JSON is used rather than pickle because it is human-readable, can be
inspected for debugging, and does not have the security concerns of
deserialising arbitrary Python objects.
"""

import json
import os


def save_index(index: dict, filepath: str) -> None:
    """
    Serialise the inverted index to a JSON file.

    Creates parent directories if they do not exist.
    Uses indent=2 for readability when inspecting the file manually.

    Args:
        index: the positional inverted index dict.
        filepath: path to write the JSON file to.

    Raises:
        OSError: if the file cannot be written (permissions, disk full, etc).
    """
    # make sure the directory exists
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
        print(f"Index saved to {filepath}")
    except OSError as e:
        print(f"Error saving index: {e}")
        raise


def load_index(filepath: str) -> dict:
    """
    Deserialise the inverted index from a JSON file.

    Args:
        filepath: path to the JSON file to read.

    Returns:
        The loaded inverted index dict.

    Raises:
        FileNotFoundError: if the file does not exist.
        json.JSONDecodeError: if the file contains invalid JSON.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            index = json.load(f)
        print(f"Index loaded from {filepath}")
        return index
    except FileNotFoundError:
        print(f"Error: index file not found at {filepath}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {filepath}: {e}")
        raise
