"""
CLI entry point for the search engine.

Commands:
    build   -- crawl the site and build the index, then save to disk
    load    -- load an existing index from disk
    print   -- print the index entry for a single word
    find    -- search the index for a query (AND or phrase)

Usage:
    python main.py build
    python main.py load
    python main.py print <word>
    python main.py find <query>
    python main.py find "exact phrase"
"""

import sys
import os

from crawler import crawl
from indexer import build_index, tokenise
from storage import save_index, load_index
from search import and_query, phrase_query, suggest_terms
from ranking import rank


# default paths and settings
START_URL = "https://quotes.toscrape.com/"
INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "index.json")
MAX_PAGES = 50


def print_usage():
    """Print the CLI usage instructions."""
    print("Search Engine CLI")
    print()
    print("Usage:")
    print("  python main.py build              Crawl and build the index")
    print("  python main.py load               Load an existing index")
    print('  python main.py print <word>        Print index entry for a word')
    print('  python main.py find <query>        Search (AND query)')
    print('  python main.py find "a phrase"     Search (phrase query)')


def print_entry(index: dict, word: str) -> None:
    """
    Pretty-print the index entry for a given word.

    Shows the word, how many documents it appears in, and for each
    document: the URL, frequency, and positions.

    Args:
        index: the positional inverted index.
        word: the word to look up.
    """
    word = word.lower()

    if word not in index:
        print(f"'{word}' not found in the index.")
        return

    entry = index[word]
    print(f"'{word}' found in {len(entry)} document(s):")
    print()

    for url, data in entry.items():
        print(f"  URL: {url}")
        print(f"  Frequency: {data['frequency']}")
        print(f"  Positions: {data['positions']}")
        print()


def handle_find(index: dict, query_parts: list[str]) -> None:
    """
    Handle the find command. Detects whether the query is a phrase
    (wrapped in quotes) or a plain AND query, runs the appropriate
    search, ranks the results, and prints them.

    Args:
        index: the positional inverted index.
        query_parts: the raw query arguments from sys.argv.
    """
    # join the query parts back together to detect quotes
    raw_query = " ".join(query_parts)

    # check if the query is a phrase (wrapped in quotes)
    is_phrase = raw_query.startswith('"') and raw_query.endswith('"')

    if is_phrase:
        # strip the surrounding quotes and tokenise
        phrase_text = raw_query.strip('"')
        terms = tokenise(phrase_text)
        print(f"Phrase query: {terms}")
        results = phrase_query(index, terms)
    else:
        terms = tokenise(raw_query)
        print(f"AND query: {terms}")
        results = and_query(index, terms)

    if not results:
        print("No results found.")

        for term in terms:
            suggestions = suggest_terms(index, term)
            if suggestions:
                print(f"  Did you mean: {', '.join(suggestions)}?")

        return

    # rank the results using TF-IDF
    ranked = rank(index, terms, results)

    print(f"\nFound {len(ranked)} result(s):\n")
    for i, (url, score) in enumerate(ranked, start=1):
        print(f"  {i}. {url}")
        print(f"     Score: {score}")
        print()


def main():
    """Main entry point. Parses sys.argv and dispatches to the right handler."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "build":
        print(f"Crawling {START_URL} (max {MAX_PAGES} pages)...")
        pages = crawl(START_URL, max_pages=MAX_PAGES)
        print(f"Building index from {len(pages)} pages...")
        index = build_index(pages)
        save_index(index, INDEX_PATH)
        print(f"Done. Index contains {len(index)} unique terms.")

    elif command == "load":
        index = load_index(INDEX_PATH)
        print(f"Index loaded with {len(index)} unique terms.")

    elif command == "print":
        if len(sys.argv) < 3:
            print("Usage: python main.py print <word>")
            return
        index = load_index(INDEX_PATH)
        print_entry(index, sys.argv[2])

    elif command == "find":
        if len(sys.argv) < 3:
            print("Usage: python main.py find <query>")
            return
        index = load_index(INDEX_PATH)
        handle_find(index, sys.argv[2:])

    else:
        print(f"Unknown command: '{command}'")
        print()
        print_usage()


if __name__ == "__main__":
    main()
