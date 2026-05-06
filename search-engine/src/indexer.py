"""
Indexer module: builds a positional inverted index from crawled page data.

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


def build_index(pages: dict[str, str]) -> dict:
    """Build a positional inverted index from a {url: text} mapping."""
    pass


def tokenise(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    pass
