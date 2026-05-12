"""
Indexer module: builds a positional inverted index from crawled page data.

The index maps each word to a dict of URLs, where each URL entry
contains the term frequency and a list of positions where the word
appears in that page's text.

Index structure:
    {
        word: {
            url: {
                "frequency": int,
                "positions": [int, ...]
            }
        }
    }
"""

import re


def tokenise(text: str) -> list[str]:
    """
    Convert text to a list of lowercase tokens.

    Strips all non-alphanumeric characters (except whitespace),
    converts to lowercase, and splits on whitespace.
    Empty strings are filtered out.

    Args:
        text: the raw text to tokenise.

    Returns:
        A list of cleaned, lowercase tokens.

    Example:
        >>> tokenise("Hello, World! 123")
        ['hello', 'world', '123']
    """
    cleaned = re.sub(r"[^a-z0-9\s]", "", text.lower())
    tokens = cleaned.split()
    return [t for t in tokens if t]


def build_index(pages: dict[str, str]) -> dict:
    """
    Build a positional inverted index from a {url: text} mapping.

    For each page, tokenises the text and records every position
    where each token appears. This enables both frequency lookups
    and phrase query matching.

    Args:
        pages: a dict mapping URLs to their raw text content.

    Returns:
        A positional inverted index dict. Structure:
        {word: {url: {"frequency": int, "positions": [int, ...]}}}
    """
    index = {}

    for url, text in pages.items():
        tokens = tokenise(text)

        for position, word in enumerate(tokens):
            # create the word entry if it does not exist yet
            if word not in index:
                index[word] = {}

            # create the url entry for this word if needed
            if url not in index[word]:
                index[word][url] = {"frequency": 0, "positions": []}

            # record this occurrence
            index[word][url]["frequency"] += 1
            index[word][url]["positions"].append(position)

    return index
