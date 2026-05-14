# Search Engine

A positional inverted index search engine built in Python. This project crawls [quotes.toscrape.com](https://quotes.toscrape.com/), builds a searchable index with positional data, and supports both AND queries and exact phrase matching with TF-IDF ranked results.

## Project Overview

This project implements a complete information retrieval pipeline: crawling, indexing, searching, and ranking. It targets quotes.toscrape.com as its document corpus, fetching up to 50 pages of quote and author data, then building a positional inverted index that supports both boolean AND queries and exact phrase matching. Results are ranked using TF-IDF to surface the most relevant documents first.

### Core Capabilities

- BFS web crawler with a configurable politeness delay (default 6 seconds between requests)
- Positional inverted index mapping each word to documents, frequencies, and token positions
- AND queries returning documents that contain all search terms
- JSON-based index persistence for offline querying without re-crawling
- 121 tests across 9 test files (unit, integration, and performance) providing 97% code coverage

### Advanced Features Beyond the Brief

The coursework specification requires a `find` command that returns pages containing given search terms. This project extends that baseline with three additional features that improve search quality:

**TF-IDF Ranking**: Rather than returning an unordered list of matching URLs, this project scores and ranks every result using Term Frequency-Inverse Document Frequency. Documents where the search terms appear frequently but are rare across the corpus are ranked highest. The ranking module (`ranking.py`) implements the standard TF-IDF formula: `score = sum of tf * log(N / df)` for each query term. This means a search for "love courage" ranks a page mentioning "courage" five times above a page mentioning it once, while downweighting ubiquitous terms like "the" that appear on every page.

**Phrase Queries**: In addition to AND queries (pages containing all terms anywhere), this project supports exact phrase matching. Searching `find "the world"` only returns pages where "the" and "world" appear as consecutive tokens, not pages where both words happen to appear separately. The phrase query algorithm uses the positional data stored in the index to verify that tokens appear at adjacent offsets (position N, position N+1, position N+2, etc.). This is implemented as a two-stage process: first an AND query narrows the candidate set, then a positional verification pass checks for consecutive positions in each candidate document.

**Query Suggestions via Edit Distance**: When a search returns no results, the system suggests similar terms from the index using Levenshtein edit distance. The `edit_distance` function computes the minimum number of single-character insertions, deletions, or substitutions needed to transform one string into another using dynamic programming. The `suggest_terms` function scans the index vocabulary and returns the closest matches, filtered by a threshold to avoid irrelevant suggestions. For example, searching for "lovee" suggests "love" and "lovely".

**Positional Inverted Index**: The index stores not just term frequencies but the exact zero-indexed token position of every occurrence of every word. This positional data is what makes phrase queries possible. A standard inverted index without positions can only answer "does this word appear in this document?" while this project's index can answer "where exactly does this word appear?" allowing the search module to verify word ordering.

## Installation

**Prerequisites**: Python 3.9 or higher.

```bash
# Clone the repository
git clone https://github.com/your-username/search-engine.git
cd search-engine

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies (runtime and development)
pip install -r requirements.txt
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| requests | 2.31.0 | HTTP requests for fetching web pages during crawling |
| beautifulsoup4 | 4.12.3 | HTML parsing and content extraction from crawled pages |
| pytest | 8.2.0 | Test framework for running the unit test suite |
| pytest-cov | 5.0.0 | Coverage reporting to measure how much code the tests exercise |

Runtime dependencies are `requests` and `beautifulsoup4`. The testing dependencies `pytest` and `pytest-cov` are only needed for running the test suite.

## Usage Examples

All commands are run from the repository root.

### Building the Index

Crawl the target site, build the positional inverted index, and save it to `data/index.json`:

```bash
python src/main.py build
```

This takes approximately 5 minutes because the crawler waits 6 seconds between requests to avoid overloading the target server. Output shows each URL as it is fetched:

```
Crawling https://quotes.toscrape.com/ (max 50 pages)...
Fetching: https://quotes.toscrape.com/
Fetching: https://quotes.toscrape.com/page/2/
...
Crawl complete. Fetched 10 pages.
Building index from 10 pages...
Done. Index contains 503 unique terms.
```

### Loading an Existing Index

Verify that a previously built index loads correctly from disk:

```bash
python src/main.py load
```

```
Index loaded with 503 unique terms.
```

### Looking Up a Word

Print the full index entry for a single word, showing which documents contain it, the frequency in each document, and the exact token positions:

```bash
python src/main.py print love
```

```
'love' found in 5 document(s):

  URL: https://quotes.toscrape.com/
  Frequency: 3
  Positions: [12, 45, 78]

  URL: https://quotes.toscrape.com/page/2/
  Frequency: 1
  Positions: [5]
```

### AND Query (with TF-IDF Ranking)

Find documents containing ALL of the given terms. Results are ranked by TF-IDF score rather than returned as an unordered list:

```bash
python src/main.py find love life
```

```
AND query: ['love', 'life']

Found 3 result(s):

  1. https://quotes.toscrape.com/page/2/
     Score: 4.2318

  2. https://quotes.toscrape.com/
     Score: 3.1074

  3. https://quotes.toscrape.com/page/5/
     Score: 1.8921
```

### Phrase Query (Exact Consecutive Matching)

Find documents where the exact phrase appears with terms in consecutive order. This goes beyond AND matching: `find "the world"` only returns pages where "the" is immediately followed by "world", verified using the positional data in the index. Wrap the phrase in quotes:

```bash
python src/main.py find "the world"
```

```
Phrase query: ['the', 'world']

Found 2 result(s):

  1. https://quotes.toscrape.com/page/3/
     Score: 2.5411

  2. https://quotes.toscrape.com/page/7/
     Score: 1.0986
```

### Query Suggestions (Automatic on No Results)

When a search returns no results, the system automatically suggests similar terms from the index using Levenshtein edit distance:

```bash
python src/main.py find lovee
```

```
AND query: ['lovee']
No results found.
  Did you mean: love, loved, lovely?
```

## Architecture Overview

This project follows a modular, functional design. Each module has a single responsibility, and modules connect through plain data structures (dictionaries and lists) rather than shared state or class hierarchies.

```
src/
  crawler.py    - BFS web crawler, fetches pages, extracts quote and author text
  indexer.py    - Tokeniser and positional inverted index builder
  storage.py    - JSON serialisation and deserialisation of the index
  search.py     - AND query, phrase query, and query suggestion logic
  ranking.py    - TF-IDF scoring and result ordering
  main.py       - CLI entry point that wires all modules together

tests/
  conftest.py          - Shared pytest fixtures (sample pages, sample index)
  test_crawler.py      - Crawler tests using mocked HTTP responses
  test_indexer.py      - Tokenisation and index construction tests
  test_storage.py      - Save/load round-trip and error handling tests
  test_search.py       - AND, phrase, edit distance, and suggestion tests
  test_ranking.py      - TF-IDF scoring and ordering tests
  test_main.py         - CLI integration tests
  test_integration.py  - End-to-end pipeline tests (crawl -> index -> search -> rank)
  test_performance.py  - Performance benchmarks with timing assertions

data/
  index.json    - The built index (generated at build time)
```

### Data Flow

The system has two primary flows:

**Build pipeline**: The CLI invokes the crawler, which performs a breadth-first traversal of the target site, following pagination links. Each fetched page is parsed with BeautifulSoup to extract quote text and author names. The resulting `{url: text}` dictionary passes to the indexer, which tokenises each document and constructs the positional inverted index. Finally, the storage module serialises the index to JSON on disk.

**Query pipeline**: The CLI loads the index from disk, then passes the user query to the search module. If the query is wrapped in quotes, phrase search runs; otherwise, AND search runs. The search module returns a list of matching URLs, which the ranking module scores using TF-IDF. Results are sorted by score and displayed.

```
Build:  CLI -> Crawler -> Indexer -> Storage -> data/index.json
Query:  CLI -> Storage -> Search -> Ranking -> Display
```

## Data Structure Explanation

### The Positional Inverted Index

The core data structure is a nested dictionary with three levels:

```json
{
  "love": {
    "https://quotes.toscrape.com/": {
      "frequency": 3,
      "positions": [12, 45, 78]
    },
    "https://quotes.toscrape.com/page/2/": {
      "frequency": 1,
      "positions": [5]
    }
  },
  "world": {
    "https://quotes.toscrape.com/page/3/": {
      "frequency": 2,
      "positions": [7, 33]
    }
  }
}
```

**Level 1** maps each unique word (lowercased, stripped of punctuation) to its postings.

**Level 2** maps each document URL to that word's occurrence data within the document.

**Level 3** contains two fields per word-document pair:
- `frequency`: the raw count of how many times the word appears in that document (used as term frequency for TF-IDF)
- `positions`: a list of zero-indexed token offsets indicating exactly where in the document the word appears (used for phrase matching)

This structure supports all four query operations in a single data format:
- **Term lookup**: Check if a word key exists
- **AND queries**: Intersect the URL key sets of multiple words
- **Phrase queries**: Retrieve position lists and verify consecutive offsets
- **TF-IDF scoring**: Read `frequency` as TF; count the number of URL keys as document frequency (DF)

### Tokenisation

The tokeniser converts raw text into index terms using two steps:

1. Remove all characters that are not lowercase letters, digits, or whitespace using the regex `[^a-z0-9\s]` applied after lowercasing
2. Split on whitespace and discard any empty strings

This approach is intentionally simple. It handles the quotes.toscrape.com corpus well but does not perform stemming, lemmatisation, or stop-word removal.

## TF-IDF Ranking (Beyond the Brief)

TF-IDF (Term Frequency-Inverse Document Frequency) is the ranking algorithm used to order search results by relevance. The coursework brief requires returning a list of pages matching a query but does not require ranking. This project adds a dedicated ranking module (`ranking.py`) so that the most relevant results appear first.

### The Formula

For each query term `t` in each matching document `d`:

```
score(d) = sum over all query terms t of: TF(t, d) * IDF(t)
```

Where:

- **TF(t, d)** = the raw frequency of term `t` in document `d` (how many times the word appears in that specific page)
- **IDF(t)** = log(N / df(t)), where N is the total number of documents in the index and df(t) is the number of documents containing term `t`

### Why This Works

TF-IDF balances two competing signals:

**Term Frequency** rewards documents where a search term appears many times. If a user searches for "love" and one document contains the word 5 times while another contains it once, the first document is likely more relevant.

**Inverse Document Frequency** penalises terms that appear in many documents. Common words like "the" or "is" appear in nearly every document, so their IDF approaches zero (log(N/N) = 0). Rare, specific terms like "universe" or "imperfection" have high IDF because they appear in few documents, making them stronger signals of relevance.

### Worked Example

Given an index of 10 documents where:
- "love" appears in 3 documents (df = 3)
- "courage" appears in 1 document (df = 1)

For a document containing "love" 2 times and "courage" 4 times:

```
TF("love") = 2
IDF("love") = log(10 / 3) = 1.2040

TF("courage") = 4
IDF("courage") = log(10 / 1) = 2.3026

score = (2 * 1.2040) + (4 * 2.3026) = 2.4080 + 9.2103 = 11.6183
```

The rare term "courage" contributes far more to the final score than the common term "love", correctly identifying this document as highly relevant for a query about courage.

## Phrase Query Algorithm (Beyond the Brief)

Phrase queries find documents where search terms appear in exact consecutive order, not just anywhere in the document. The coursework brief requires a `find` command that matches pages containing all given words (an AND query). This project adds phrase query support on top of that: wrapping a query in quotes (e.g., `find "the world"`) triggers positional matching rather than simple term intersection.

### How It Works

The phrase query algorithm operates in two stages:

**Stage 1 (Candidate filtering)**: Run an AND query to find documents containing all terms. This narrows the search space before the more expensive positional check.

**Stage 2 (Position verification)**: For each candidate document, retrieve the position list for every term in the phrase. Then check whether any starting position in the first term's list leads to a valid consecutive chain.

### The Position Checking Algorithm

Given a phrase of N terms, the algorithm:

1. Takes the position list for each term in a candidate document
2. Converts all position lists (except the first) to sets for O(1) membership testing
3. For each starting position `p` in the first term's positions:
   - Checks if `p + 1` exists in the second term's position set
   - Checks if `p + 2` exists in the third term's position set
   - Continues for all N terms
4. If any starting position produces a complete chain, the document matches

### Worked Example

Searching for the phrase "the world" in a document where:
- "the" appears at positions [0, 5, 12]
- "world" appears at positions [6, 20]

The algorithm checks:
- Start at position 0: is "world" at position 1? No.
- Start at position 5: is "world" at position 6? Yes. Match found.
- (Position 12 is not checked because a match was already found.)

This document contains the phrase "the world" because the two words appear consecutively at positions 5 and 6.

## Query Suggestions Algorithm (Beyond the Brief)

When a search returns no results, the system suggests similar terms from the index. This helps users recover from typos and misspellings without manually browsing the index vocabulary. The coursework brief does not require query suggestions, but the feature is a natural extension of the search interface.

### Levenshtein Edit Distance

The suggestion system uses Levenshtein edit distance to measure similarity between strings. The edit distance between two strings is the minimum number of single-character operations (insertion, deletion, or substitution) needed to transform one into the other.

The implementation uses a space-optimised dynamic programming approach that stores only two rows of the distance matrix at a time, reducing memory usage from O(m * n) to O(n) where m and n are the lengths of the two strings.

### How Suggestions Work

1. For each query term that produced no results, scan every word in the index
2. Skip words whose length differs from the query term by more than the threshold (early pruning to avoid unnecessary distance calculations)
3. Compute the edit distance between the query term and each remaining index word
4. Filter to words within a threshold of `max(len(term) // 2 + 1, 2)` edits
5. Sort by distance (closest first), then alphabetically for ties
6. Return the top N suggestions

### Worked Example

Searching for "lovee" against an index containing "love", "lovely", "loved", "life", "world":
- edit_distance("lovee", "love") = 1 (delete the extra 'e')
- edit_distance("lovee", "lovely") = 2 (substitute 'e' for 'l', insert 'y')
- edit_distance("lovee", "loved") = 2 (substitute 'e' for 'd')
- edit_distance("lovee", "life") = 3 (exceeds threshold, filtered out)
- edit_distance("lovee", "world") = 5 (length difference too large, skipped entirely)

Result: suggestions are ["love", "loved", "lovely"], sorted by distance.

## Testing Instructions

### Running the Full Test Suite

The test configuration in `pyproject.toml` automatically enables verbose output and coverage reporting:

```bash
python -m pytest
```

This runs all 121 tests and prints a coverage report showing which lines in each source file are exercised.

### Running a Specific Test File

```bash
pytest tests/test_search.py -v
```

### Running a Single Test Function

```bash
pytest tests/test_ranking.py::test_rare_term_scores_higher -v
```

### Test Coverage Summary

| Module | What the Tests Verify |
|--------|----------------------|
| crawler.py | Text extraction from HTML, pagination link following, politeness delay, error handling for failed requests, duplicate URL prevention |
| indexer.py | Lowercase conversion, punctuation removal, number preservation, position tracking, frequency counting, multi-document indexing |
| storage.py | JSON round-trip integrity, directory creation, FileNotFoundError on missing files, JSONDecodeError on corrupt files |
| search.py | AND query set intersection, single-term queries, missing terms returning empty results, phrase position verification with multiple position candidates, edit distance correctness, suggestion ranking and filtering |
| ranking.py | TF-IDF score calculation, rare terms scoring higher than common terms, multi-term score summation, stable sort ordering, empty input handling |
| main.py | CLI command routing, AND vs phrase query detection based on quotes, output formatting |
| (integration) | Full build pipeline (crawl to disk round-trip), full query pipeline (index to ranked results), query suggestions through the pipeline, edge cases (empty corpus, single page, special characters, case insensitivity) |
| (performance) | Index build timing at 10/100/1000 page scales, linear scaling verification, AND and phrase query throughput, ranking speed, suggestion lookup speed |

### Testing Approach

The test suite uses three categories of tests:

**Unit tests** verify individual functions in isolation. The crawler tests use `unittest.mock` to patch HTTP requests, preventing live network calls. All other modules are tested with constructed dictionaries that mimic the real index structure but contain controlled, predictable data. Shared fixtures are defined in `conftest.py`.

**Integration tests** verify that modules work together correctly by running multi-step workflows. These test the full build pipeline (mocked crawl through to disk persistence and reload) and the full query pipeline (index construction through search and ranking to final result ordering).

**Performance benchmarks** measure execution time of key operations across varying corpus sizes. Synthetic corpora of 10 to 1000 pages are generated, and tests assert that operations complete within reasonable time bounds. A linear scaling test verifies that index building time grows proportionally with corpus size rather than exponentially.

## Performance Notes

**Crawl time**: Approximately 5 minutes for 50 pages. The 6-second politeness delay between requests is the dominant factor. The crawler is single-threaded by design because the politeness delay makes parallelisation irrelevant for this corpus size.

**Index build time**: Negligible (milliseconds). Tokenisation and dictionary insertion are linear in the total token count across all documents.

**Index size on disk**: Approximately 200 KB as formatted JSON for 50 pages of quotes.

**AND query time**: Proportional to the number of query terms. Each term lookup is O(1) in the top-level dictionary. Set intersection across terms is O(min(|posting list sizes|)).

**Phrase query time**: After the AND query narrows candidates, the positional check iterates through starting positions of the first term and performs O(1) set lookups for subsequent terms. Worst case is O(p1 * n) where p1 is the number of positions of the first term and n is the number of phrase terms.

**TF-IDF ranking**: O(r * t) where r is the number of results and t is the number of query terms. Each score computation involves a dictionary lookup and a single floating-point multiplication.

**Query suggestions**: O(V * max(len(term), len(word))) where V is the vocabulary size. Each suggestion lookup computes edit distance against index terms that pass the length filter. For a 500-term index, 100 suggestion lookups complete in under 5 seconds.

**Memory usage**: The entire index is loaded into memory. At 200 KB for 50 pages, this is trivial. The approach would not scale to millions of documents without partitioning or streaming.

### Benchmark Results

The performance test suite (`tests/test_performance.py`) generates synthetic corpora and measures execution time. Representative results:

| Operation | Scale | Time |
|-----------|-------|------|
| Index build | 10 pages (1,000 tokens) | < 0.1s |
| Index build | 100 pages (10,000 tokens) | < 0.5s |
| Index build | 1,000 pages (100,000 tokens) | < 5.0s |
| AND query | 1,000 queries against 500-page index | < 1.0s |
| Phrase query | 1,000 queries against 500-page index | < 2.0s |
| TF-IDF ranking | 100x ranking of 500 results | < 1.0s |
| Query suggestions | 100 lookups against 500-page index | < 5.0s |

The linear scaling test confirms that building a 500-page index takes less than 20x the time of a 50-page index, consistent with O(n) complexity.

## Future Improvements

- Add stemming (e.g., Porter Stemmer) so that queries for "running" also match "run" and "runs"
- Implement stop-word removal to reduce index size and improve ranking precision by filtering out terms like "the", "is", and "a"
- Add sublinear TF scaling (log(1 + tf)) to prevent very long documents from dominating results purely through repetition
- Support document-length normalisation to fairly compare documents of different sizes
- Add incremental indexing so that new pages can be added without rebuilding the entire index from scratch
- Implement a robots.txt parser to respect crawler directives programmatically
- Add proximity scoring for AND queries, ranking documents higher when search terms appear near each other
- Support wildcard queries (e.g., "lov*" matching "love", "loved", "lovely")
- Add a web interface for interactive searching rather than CLI-only access
- Implement index compression (e.g., variable-byte encoding for position lists) to reduce disk and memory footprint at larger scales

## Design Decisions

See [DECISIONS.md](DECISIONS.md) for detailed design rationale and trade-off analysis.
