"""
Ranking module: scores documents using TF-IDF.

TF (Term Frequency) measures how often a term appears in a document.
IDF (Inverse Document Frequency) measures how rare a term is across
all documents. Multiplying them together gives higher scores to
documents where the search terms appear frequently but are rare
across the collection.
"""

import math


def get_doc_count(index: dict) -> int:
    """
    Count the total number of unique documents in the index.

    Scans all words in the index and collects every unique URL.

    Args:
        index: the positional inverted index.

    Returns:
        The number of unique documents (URLs) in the index.
    """
    all_urls = set()
    for word_data in index.values():
        all_urls.update(word_data.keys())
    return len(all_urls)


def rank(index: dict, terms: list[str], matching_urls: list[str]) -> list[tuple[str, float]]:
    """
    Rank matching URLs by their TF-IDF score for the given search terms.

    For each URL, computes the sum of TF-IDF scores across all query
    terms. TF is calculated as the raw frequency of the term in the
    document. IDF is calculated as log(N / df) where N is the total
    number of documents and df is the number of documents containing
    the term.

    Args:
        index: the positional inverted index.
        terms: the list of query terms.
        matching_urls: URLs to score (from a search query).

    Returns:
        A list of (url, score) tuples sorted by score descending.
    """
    if not matching_urls or not terms:
        return []

    total_docs = get_doc_count(index)

    # avoid division by zero if index is empty
    if total_docs == 0:
        return []

    scored = []

    for url in matching_urls:
        score = 0.0

        for term in terms:
            if term not in index or url not in index[term]:
                continue

            # TF: how often does this term appear in this document
            tf = index[term][url]["frequency"]

            # DF: how many documents contain this term
            df = len(index[term])

            # IDF: log(total_docs / df), rarer terms score higher
            idf = math.log(total_docs / df)

            score += tf * idf

        scored.append((url, round(score, 4)))

    # sort by score descending, then by URL for stable ordering
    scored.sort(key=lambda x: (-x[1], x[0]))

    return scored
