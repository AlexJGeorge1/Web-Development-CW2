"""
Performance benchmarks for the search engine.

These tests measure execution time of key operations across varying
corpus sizes to verify that performance scales as expected. Each test
prints timing results for visibility in test output.
"""

import random
import string
import time

from indexer import build_index
from search import and_query, phrase_query, suggest_terms
from ranking import rank


def generate_corpus(num_pages: int, words_per_page: int = 100) -> dict[str, str]:
    """
    Generate a synthetic corpus of random text for benchmarking.

    Uses a fixed vocabulary of 500 words to ensure term overlap across
    pages, which is necessary for meaningful search and ranking tests.

    Args:
        num_pages: number of pages to generate.
        words_per_page: number of words per page.

    Returns:
        A dict mapping synthetic URLs to random text.
    """
    vocab = [
        "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
        for _ in range(500)
    ]

    pages = {}
    for i in range(num_pages):
        words = [random.choice(vocab) for _ in range(words_per_page)]
        pages[f"http://example.com/page/{i}/"] = " ".join(words)

    return pages


class TestIndexBuildPerformance:
    """Benchmark index building at different corpus sizes."""

    def test_build_10_pages(self):
        """Index building for 10 pages should complete in under 0.1 seconds."""
        pages = generate_corpus(10)

        start = time.perf_counter()
        index = build_index(pages)
        elapsed = time.perf_counter() - start

        print(f"\n  Build 10 pages: {elapsed:.4f}s ({len(index)} terms)")
        assert elapsed < 0.1
        assert len(index) > 0

    def test_build_100_pages(self):
        """Index building for 100 pages should complete in under 0.5 seconds."""
        pages = generate_corpus(100)

        start = time.perf_counter()
        index = build_index(pages)
        elapsed = time.perf_counter() - start

        print(f"\n  Build 100 pages: {elapsed:.4f}s ({len(index)} terms)")
        assert elapsed < 0.5

    def test_build_1000_pages(self):
        """Index building for 1000 pages should complete in under 5 seconds."""
        pages = generate_corpus(1000)

        start = time.perf_counter()
        index = build_index(pages)
        elapsed = time.perf_counter() - start

        print(f"\n  Build 1000 pages: {elapsed:.4f}s ({len(index)} terms)")
        assert elapsed < 5.0

    def test_build_scales_linearly(self):
        """Building time should scale roughly linearly with corpus size."""
        pages_small = generate_corpus(50)
        pages_large = generate_corpus(500)

        start = time.perf_counter()
        build_index(pages_small)
        time_small = time.perf_counter() - start

        start = time.perf_counter()
        build_index(pages_large)
        time_large = time.perf_counter() - start

        ratio = time_large / max(time_small, 0.0001)
        print(f"\n  50 pages: {time_small:.4f}s, 500 pages: {time_large:.4f}s, ratio: {ratio:.1f}x (expected ~10x)")
        assert ratio < 20


class TestQueryPerformance:
    """Benchmark query execution against a large index."""

    def setup_method(self):
        """Build a large index for query benchmarks."""
        random.seed(42)
        self.pages = generate_corpus(500, words_per_page=200)
        self.index = build_index(self.pages)
        self.terms = list(self.index.keys())

    def test_and_query_speed(self):
        """1000 AND queries should complete in under 1 second."""
        query_terms = [
            [random.choice(self.terms) for _ in range(2)]
            for _ in range(1000)
        ]

        start = time.perf_counter()
        for terms in query_terms:
            and_query(self.index, terms)
        elapsed = time.perf_counter() - start

        print(f"\n  1000 AND queries: {elapsed:.4f}s ({elapsed/1000*1000:.2f}ms each)")
        assert elapsed < 1.0

    def test_phrase_query_speed(self):
        """1000 phrase queries should complete in under 2 seconds."""
        query_terms = [
            [random.choice(self.terms) for _ in range(2)]
            for _ in range(1000)
        ]

        start = time.perf_counter()
        for terms in query_terms:
            phrase_query(self.index, terms)
        elapsed = time.perf_counter() - start

        print(f"\n  1000 phrase queries: {elapsed:.4f}s ({elapsed/1000*1000:.2f}ms each)")
        assert elapsed < 2.0

    def test_ranking_speed(self):
        """Ranking 500 results should complete in under 0.1 seconds."""
        all_urls = list(self.pages.keys())
        terms = [random.choice(self.terms) for _ in range(3)]

        start = time.perf_counter()
        for _ in range(100):
            rank(self.index, terms, all_urls)
        elapsed = time.perf_counter() - start

        print(f"\n  100x rank 500 results: {elapsed:.4f}s ({elapsed/100*1000:.2f}ms each)")
        assert elapsed < 1.0

    def test_suggestion_speed(self):
        """100 suggestion lookups should complete in under 5 seconds."""
        misspelled = [t + "x" for t in random.sample(self.terms, min(100, len(self.terms)))]

        start = time.perf_counter()
        for term in misspelled:
            suggest_terms(self.index, term, max_suggestions=5)
        elapsed = time.perf_counter() - start

        print(f"\n  100 suggestion lookups: {elapsed:.4f}s ({elapsed/100*1000:.2f}ms each)")
        assert elapsed < 5.0
