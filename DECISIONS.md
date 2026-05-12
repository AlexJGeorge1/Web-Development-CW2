# Design Decisions and GenAI Considerations

## Overview

This document records key design decisions made during the development of this
search engine, including where generative AI was used, its limitations, and
critical evaluations of the generated output.

## Decision 1: Functional Design Over OOP

**Choice**: Use standalone functions in each module instead of classes.

**Rationale**: For a project of this size, classes would add indirection without
meaningful benefit. Functions are easier to test in isolation, easier to read,
and easier to explain in a walkthrough. Each module (crawler, indexer, etc.)
acts as a namespace, which gives the same organisational benefit.

**GenAI consideration**: An AI assistant might suggest a class-based design
(e.g. `SearchEngine` class, `Crawler` class) because class-based patterns are
overrepresented in training data and typical of "production" code. For this
coursework scope, that would be over-engineering.

**Potential pushback**: "Without classes, how would you extend this to support
multiple index backends?" Response: At this scale, a simple refactor to
introduce a class later is trivial. YAGNI (You Aren't Gonna Need It) applies.

## Decision 2: sys.argv Over argparse

**Choice**: Parse commands using `sys.argv` directly rather than the `argparse`
library.

**Rationale**: The CLI has exactly 4 commands with minimal arguments. `argparse`
adds boilerplate and a learning curve for something achievable in a few lines.
This keeps the CLI code transparent and easy to trace.

**GenAI consideration**: AI tools tend to default to `argparse` or even `click`
because those appear heavily in training data. For 4 simple commands, that is
unnecessary complexity. However, if the CLI grew to 10+ commands with flags,
`argparse` would become the right choice.

**Potential pushback**: "argparse gives you --help for free." Response: True,
but we print a manual usage message in the else branch, which serves the same
purpose for this scope.

## Decision 3: JSON Storage Over Pickle

**Choice**: Store the index as a JSON file, not Python pickle.

**Rationale**: JSON is human-readable and can be inspected/debugged manually.
Pickle is Python-specific, not inspectable, and has security concerns
(arbitrary code execution on load). The trade-off is file size: JSON is larger,
but for an index of ~50 pages, this is negligible.

**GenAI consideration**: AI might suggest pickle for "performance" or
"simplicity". This would be a poor choice for a coursework project where the
marker may want to inspect the index file. JSON makes the data transparent.

**Potential pushback**: "JSON cannot serialise sets or tuples natively."
Response: Our index uses only dicts, lists, strings, and integers, which are
all natively JSON-serialisable. No custom encoder needed.

## Decision 4: BFS Crawling Strategy

**Choice**: Use breadth-first search to discover pages.

**Rationale**: BFS explores the site level by level, which is natural for a
paginated site like quotes.toscrape.com (page 1 links to page 2, etc.). DFS
would work too, but BFS gives a more predictable crawl order and is slightly
easier to reason about.

**GenAI consideration**: AI might not consider the specific structure of
quotes.toscrape.com when choosing a traversal strategy. A human developer would
inspect the site first and notice it is essentially a linear pagination, making
BFS the natural fit.

**Potential pushback**: "Why not use an async crawler for performance?"
Response: With a mandatory 6-second delay between requests, async provides
zero benefit. We are I/O-bound by the politeness constraint, not by network
latency.

## Decision 5: Regex-Based Tokenisation

**Choice**: Use `re.sub` to strip non-alphanumeric characters, then split on
whitespace.

**Rationale**: Simple, fast, and sufficient for the quotes.toscrape.com domain,
which contains plain English text. No need for NLTK or spaCy tokenisers.

**GenAI consideration**: AI tools might suggest NLTK tokenisers or stemming
(e.g. Porter stemmer). While stemming improves recall, it adds a dependency
and complexity that is not required by the specification. The spec asks for
"clean tokenisation", not NLP-grade processing.

**Potential pushback**: "Won't you miss hyphenated words like 'well-known'?"
Response: Yes, "well-known" becomes ["well", "known"]. This is acceptable for
this coursework. A production system might handle hyphens differently.

**Limitation noted**: The tokeniser does not handle contractions well. "don't"
becomes "dont". A more robust approach would split on apostrophes or use a
library, but this is out of scope.

## Decision 6: TF-IDF Without Normalisation

**Choice**: Use raw TF-IDF (term frequency times inverse document frequency)
without length normalisation or sublinear TF scaling.

**Rationale**: The standard TF-IDF formula is well understood, easy to
implement, and meets the specification. Advanced variants (BM25, sublinear TF)
would improve ranking quality but add complexity beyond what the spec requires.

**GenAI consideration**: AI might generate a BM25 implementation because it is
"better". For a 50-page index of short quotes, the difference is negligible,
and the added complexity would be harder to explain in a video walkthrough.

**Potential pushback**: "Longer documents will always score higher because TF
is not normalised." Response: On quotes.toscrape.com, all pages have
approximately similar length (10 quotes per page), so length bias is minimal.

## Decision 7: No Concurrency in Crawler

**Choice**: Single-threaded, synchronous crawler.

**Rationale**: The 6-second politeness delay means we can only make one request
every 6 seconds regardless of threading. Adding concurrency would not speed
anything up and would only complicate the code.

**GenAI consideration**: AI assistants sometimes add `asyncio` or threading by
default for crawlers. This is a case where understanding the constraint
(politeness delay) should override the default pattern.

## Decision 8: Phrase Query via Positional Matching

**Choice**: Detect phrase queries by checking for surrounding quotes in the CLI
input, then verify consecutive positions in the index.

**Rationale**: This is the standard approach for phrase queries in information
retrieval. The positional inverted index stores exactly the data needed. The
algorithm checks that for each pair of adjacent terms, there exists a position
sequence where each term's position is exactly one more than the previous.

**GenAI consideration**: An AI might implement this correctly but could miss
edge cases such as a term appearing multiple times in a document (requiring
checking all position combinations). The implementation needs to handle the
case where a word appears at positions [2, 7, 15] and we need to find if any
of those positions works in the chain.

**Potential pushback**: "Why not use n-gram indexing instead?" Response:
Positional indexing is more space-efficient and flexible. It supports arbitrary
phrase lengths without building separate n-gram indices.

## Summary of Limitations

1. **No robots.txt parsing**: hardcode the politeness delay rather than
   reading the site's robots.txt. A production crawler should respect robots.txt
   directives.

2. **No duplicate content detection**: If two URLs serve identical content,
   both are indexed. A production system would hash content to detect duplicates.

3. **No incremental indexing**: The full index is rebuilt from scratch each time.
   A production system would support incremental updates.

4. **Fixed tokenisation**: No stemming, no stop-word removal, no handling of
   Unicode beyond ASCII alphanumerics.

5. **Memory-bound**: The entire index is loaded into memory. For a 50-page site
   this is fine; for millions of pages it would not scale.

6. **Test coverage of crawler depends on mocking**:  cannot unit-test the
   crawler against the live site reliably. Tests use mock HTTP responses, which
   means bugs in HTML parsing of the real site might not be caught.
