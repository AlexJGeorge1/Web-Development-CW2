# Search Engine

A positional inverted index search engine built in Python for the COMP module coursework.

Crawls [quotes.toscrape.com](https://quotes.toscrape.com/), builds a searchable index, and supports ranked keyword and phrase queries.

## Features

- BFS web crawler with configurable politeness delay (default 6 seconds)
- Positional inverted index: `word -> {url -> {frequency, positions}}`
- AND queries (documents containing all terms)
- Phrase queries (documents containing terms in exact order)
- TF-IDF ranking of search results
- JSON-based index persistence
- Comprehensive test suite with >85% coverage

## Setup

```bash
# create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

## Usage

All commands are run from the repository root:

### Build the index

Crawls the site and saves the index to `data/index.json`:

```bash
python src/main.py build
```

This will take several minutes due to the 6-second politeness delay between requests.

### Load the index

Verify that a previously built index can be loaded:

```bash
python src/main.py load
```

### Look up a word

Print the full index entry for a single word, showing which documents contain it, how many times, and at what positions:

```bash
python src/main.py print love
```

### Search: AND query

Find documents containing ALL of the given terms, ranked by TF-IDF score:

```bash
python src/main.py find love life
```

### Search: phrase query

Find documents where the exact phrase appears (terms consecutive in order). Wrap the phrase in quotes:

```bash
python src/main.py find "the world"
```

## Architecture

```
src/
  crawler.py    - BFS web crawler, fetches pages, extracts text
  indexer.py    - Tokeniser and positional inverted index builder
  storage.py    - JSON serialisation/deserialisation of the index
  search.py     - AND queries and phrase queries
  ranking.py    - TF-IDF scoring and result ranking
  main.py       - CLI entry point wiring everything together
tests/
  test_crawler.py   - Crawler tests (mocked HTTP)
  test_indexer.py   - Tokeniser and index builder tests
  test_storage.py   - Save/load and error handling tests
  test_search.py    - AND and phrase query tests
  test_ranking.py   - TF-IDF scoring tests
data/
  index.json    - The built index (generated, not committed)
```

### Data Flow

1. **Build**: CLI -> Crawler (fetches HTML pages) -> Indexer (tokenises and builds index) -> Storage (saves to JSON)
2. **Find**: CLI -> Storage (loads index) -> Search (AND or phrase query) -> Ranking (TF-IDF scoring) -> CLI (displays results)

### Index Structure

The positional inverted index maps each word to a dictionary of documents:

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
  }
}
```

This structure supports:
- **Frequency lookups**: How often does a word appear in a given document
- **AND queries**: Set intersection of URL keys across terms
- **Phrase queries**: Check if positions are consecutive across terms
- **TF-IDF**: Use frequency as TF, count of URL entries as DF

## Testing

Run the full test suite with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Run a specific test file:

```bash
pytest tests/test_indexer.py -v
```

## Design Decisions

See [DECISIONS.md](DECISIONS.md) for detailed design rationale, GenAI considerations, and trade-off analysis.
