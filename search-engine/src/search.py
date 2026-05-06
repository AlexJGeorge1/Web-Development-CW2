"""
Search module: AND queries and phrase queries over the inverted index.
"""


def and_query(index: dict, terms: list[str]) -> list[str]:
    """Return URLs containing ALL terms."""
    pass


def phrase_query(index: dict, terms: list[str]) -> list[str]:
    """Return URLs where terms appear consecutively (using positions)."""
    pass
