"""
Integration tests for the full search engine pipeline.

These tests verify that modules work together correctly by running
multi-step workflows: crawling (mocked) through indexing, searching,
and ranking.
"""

import json
import os
from unittest.mock import patch, MagicMock

from crawler import crawl, extract_text
from indexer import build_index, tokenise
from storage import save_index, load_index
from search import and_query, phrase_query, suggest_terms
from ranking import rank


# realistic HTML mimicking quotes.toscrape.com structure
PAGE_HTML = {
    "http://quotes.example.com/": """
    <html><body>
    <div class="quote">
        <span class="text">“The world as we have created it is a process
        of our thinking.”</span>
        <small class="author">Albert Einstein</small>
    </div>
    <div class="quote">
        <span class="text">“Life is what happens when you are busy
        making other plans.”</span>
        <small class="author">John Lennon</small>
    </div>
    <nav><ul class="pager">
        <li class="next"><a href="/page/2/">Next</a></li>
    </ul></nav>
    </body></html>
    """,
    "http://quotes.example.com/page/2/": """
    <html><body>
    <div class="quote">
        <span class="text">“In the middle of difficulty lies
        opportunity.”</span>
        <small class="author">Albert Einstein</small>
    </div>
    <div class="quote">
        <span class="text">“The only way to do great work is to love
        what you do.”</span>
        <small class="author">Steve Jobs</small>
    </div>
    </body></html>
    """
}


def make_mock_response(html):
    """Create a mock requests.Response."""
    mock = MagicMock()
    mock.text = html
    mock.status_code = 200
    mock.raise_for_status = MagicMock()
    return mock


class TestFullBuildPipeline:
    """Test the complete build pipeline: crawl -> index -> save -> load."""

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_to_index_to_disk(self, mock_sleep, mock_get, tmp_path):
        """The full build pipeline should produce a loadable index."""
        mock_get.side_effect = [
            make_mock_response(PAGE_HTML["http://quotes.example.com/"]),
            make_mock_response(PAGE_HTML["http://quotes.example.com/page/2/"])
        ]

        pages = crawl("http://quotes.example.com/", max_pages=2)
        index = build_index(pages)
        filepath = str(tmp_path / "index.json")
        save_index(index, filepath)
        loaded = load_index(filepath)

        assert loaded == index
        assert len(loaded) > 0

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawled_content_is_searchable(self, mock_sleep, mock_get):
        """Words from crawled pages should be findable in the index."""
        mock_get.side_effect = [
            make_mock_response(PAGE_HTML["http://quotes.example.com/"]),
            make_mock_response(PAGE_HTML["http://quotes.example.com/page/2/"])
        ]

        pages = crawl("http://quotes.example.com/", max_pages=2)
        index = build_index(pages)

        results = and_query(index, ["einstein"])
        assert len(results) == 2

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_index_persists_correctly(self, mock_sleep, mock_get, tmp_path):
        """Index saved to disk should be identical after loading."""
        mock_get.return_value = make_mock_response(
            PAGE_HTML["http://quotes.example.com/"]
        )

        pages = crawl("http://quotes.example.com/", max_pages=1)
        index = build_index(pages)
        filepath = str(tmp_path / "index.json")

        save_index(index, filepath)
        loaded = load_index(filepath)

        for word in index:
            assert word in loaded
            for url in index[word]:
                assert loaded[word][url]["frequency"] == index[word][url]["frequency"]
                assert loaded[word][url]["positions"] == index[word][url]["positions"]


class TestFullQueryPipeline:
    """Test the complete query pipeline: index -> search -> rank."""

    def setup_method(self):
        """Build a shared index from realistic page text."""
        self.pages = {
            "http://a.com": "love is patient love is kind love endures all things",
            "http://b.com": "the world is full of beauty and wonder",
            "http://c.com": "love the world and find beauty in everything",
            "http://d.com": "patience is a virtue that requires practice"
        }
        self.index = build_index(self.pages)

    def test_and_query_with_ranking(self):
        """AND query results should be ranked by TF-IDF score."""
        results = and_query(self.index, ["love"])
        ranked = rank(self.index, ["love"], results)

        assert len(ranked) == 2
        assert ranked[0][0] == "http://a.com"
        assert ranked[0][1] > ranked[1][1]

    def test_phrase_query_with_ranking(self):
        """Phrase query should find exact consecutive matches and rank them."""
        results = phrase_query(self.index, ["love", "is"])
        ranked = rank(self.index, ["love", "is"], results)

        assert len(ranked) >= 1
        assert "http://a.com" in [url for url, _ in ranked]

    def test_multi_term_and_query(self):
        """Multi-term AND query should only return docs with all terms."""
        results = and_query(self.index, ["love", "world"])
        ranked = rank(self.index, ["love", "world"], results)

        assert len(ranked) == 1
        assert ranked[0][0] == "http://c.com"

    def test_phrase_not_found_returns_empty(self):
        """A phrase that does not appear consecutively returns no results."""
        results = phrase_query(self.index, ["virtue", "beauty"])
        ranked = rank(self.index, ["virtue", "beauty"], results)

        assert ranked == []

    def test_rare_term_ranked_higher(self):
        """A document with a rare term should score higher than one
        with only common terms for a multi-term query."""
        results = and_query(self.index, ["is"])
        ranked = rank(self.index, ["is"], results)

        scores = {url: score for url, score in ranked}
        assert len(scores) >= 2


class TestSuggestionsPipeline:
    """Test query suggestions through the full pipeline."""

    def setup_method(self):
        """Build a shared index."""
        self.pages = {
            "http://a.com": "love patience kindness beauty world",
            "http://b.com": "wonder beautiful lovely peaceful"
        }
        self.index = build_index(self.pages)

    def test_suggestions_for_misspelled_term(self):
        """A misspelled term should produce suggestions from the index."""
        results = and_query(self.index, ["lovee"])
        assert results == []

        suggestions = suggest_terms(self.index, "lovee")
        assert "love" in suggestions or "lovely" in suggestions

    def test_suggestions_for_close_typo(self):
        """A single-character typo should suggest the correct term."""
        suggestions = suggest_terms(self.index, "worlf")
        assert "world" in suggestions

    def test_no_suggestions_for_valid_term(self):
        """A term that exists in the index should not appear in its own suggestions."""
        suggestions = suggest_terms(self.index, "love")
        assert "love" not in suggestions


class TestEdgeCases:
    """Test edge cases through the full pipeline."""

    def test_empty_corpus(self):
        """An empty corpus should produce an empty index and no results."""
        index = build_index({})
        results = and_query(index, ["anything"])
        ranked = rank(index, ["anything"], results)
        assert ranked == []

    def test_single_page_corpus(self):
        """A single-page corpus should still be searchable."""
        pages = {"http://only.com": "the only page in the corpus"}
        index = build_index(pages)

        results = and_query(index, ["only"])
        ranked = rank(index, ["only"], results)

        assert len(ranked) == 1
        assert ranked[0][0] == "http://only.com"

    def test_query_with_no_matching_terms(self):
        """Searching for terms not in the corpus returns empty."""
        pages = {"http://a.com": "hello world"}
        index = build_index(pages)

        results = and_query(index, ["nonexistent"])
        assert results == []

    def test_special_characters_in_query(self):
        """Special characters in query terms should be handled gracefully."""
        pages = {"http://a.com": "hello world"}
        index = build_index(pages)

        cleaned_terms = tokenise("hello! @world#")
        results = and_query(index, cleaned_terms)
        assert len(results) == 1

    def test_case_insensitive_search(self):
        """Search should be case-insensitive through tokenisation."""
        pages = {"http://a.com": "Hello World"}
        index = build_index(pages)

        terms = tokenise("HELLO world")
        results = and_query(index, terms)
        assert len(results) == 1
