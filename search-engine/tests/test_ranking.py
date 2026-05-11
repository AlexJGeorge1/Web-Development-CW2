"""
Tests for the ranking module: TF-IDF scoring.
"""

import math
import pytest

from ranking import rank, get_doc_count


# sample index with 3 documents
# "love" appears in 1 doc (rare, high IDF)
# "the" appears in all 3 docs (common, low IDF)
SAMPLE_INDEX = {
    "the": {
        "http://a.com": {"frequency": 3, "positions": [0, 2, 5]},
        "http://b.com": {"frequency": 2, "positions": [0, 4]},
        "http://c.com": {"frequency": 1, "positions": [0]}
    },
    "world": {
        "http://a.com": {"frequency": 1, "positions": [1]},
        "http://b.com": {"frequency": 1, "positions": [1]}
    },
    "love": {
        "http://a.com": {"frequency": 5, "positions": [3, 6, 7, 8, 9]}
    },
    "life": {
        "http://b.com": {"frequency": 2, "positions": [2, 5]},
        "http://c.com": {"frequency": 1, "positions": [1]}
    }
}


class TestGetDocCount:
    """Tests for get_doc_count helper."""

    def test_counts_unique_urls(self):
        """Should count 3 unique URLs across the index."""
        assert get_doc_count(SAMPLE_INDEX) == 3

    def test_empty_index(self):
        """An empty index has 0 documents."""
        assert get_doc_count({}) == 0

    def test_single_word_single_doc(self):
        """A minimal index with one word in one doc."""
        index = {"hello": {"http://x.com": {"frequency": 1, "positions": [0]}}}
        assert get_doc_count(index) == 1


class TestRank:
    """Tests for the rank function."""

    def test_rare_term_scores_higher(self):
        """A rare term (love, in 1/3 docs) should give a higher score
        than a common term (the, in 3/3 docs)."""
        # score for "love" in a.com: tf=5, idf=log(3/1)=1.098, score=5.49
        # score for "the" in a.com: tf=3, idf=log(3/3)=0, score=0
        love_results = rank(SAMPLE_INDEX, ["love"], ["http://a.com"])
        the_results = rank(SAMPLE_INDEX, ["the"], ["http://a.com"])

        # "the" appears in all 3 docs so idf = log(3/3) = 0
        assert the_results[0][1] == 0.0
        # "love" is rare so its score should be positive
        assert love_results[0][1] > 0

    def test_higher_frequency_scores_higher(self):
        """Between two docs, the one with higher term frequency should
        score higher for the same term."""
        results = rank(SAMPLE_INDEX, ["life"], ["http://b.com", "http://c.com"])

        # b.com has frequency=2 for "life", c.com has frequency=1
        # both have same IDF, so b.com should score higher
        assert results[0][0] == "http://b.com"
        assert results[1][0] == "http://c.com"
        assert results[0][1] > results[1][1]

    def test_results_sorted_descending(self):
        """Results should be sorted by score in descending order."""
        results = rank(SAMPLE_INDEX, ["life"], ["http://b.com", "http://c.com"])
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_multi_term_scores_sum(self):
        """Multi-term query scores should sum TF-IDF across terms."""
        # a.com has both "world" and "love"
        single_world = rank(SAMPLE_INDEX, ["world"], ["http://a.com"])
        single_love = rank(SAMPLE_INDEX, ["love"], ["http://a.com"])
        combined = rank(SAMPLE_INDEX, ["world", "love"], ["http://a.com"])

        expected = single_world[0][1] + single_love[0][1]
        assert combined[0][1] == pytest.approx(expected, abs=0.001)

    def test_empty_matching_urls(self):
        """No matching URLs should return an empty list."""
        results = rank(SAMPLE_INDEX, ["the"], [])
        assert results == []

    def test_empty_terms(self):
        """No search terms should return an empty list."""
        results = rank(SAMPLE_INDEX, [], ["http://a.com"])
        assert results == []

    def test_term_not_in_index(self):
        """A term not in the index should contribute 0 to the score."""
        results = rank(SAMPLE_INDEX, ["nonexistent"], ["http://a.com"])
        assert results[0][1] == 0.0

    def test_idf_calculation(self):
        """Verify the IDF value for a specific term manually."""
        # "world" appears in 2 of 3 docs, so idf = log(3/2)
        expected_idf = math.log(3 / 2)
        # a.com has frequency=1 for "world", so score = 1 * log(3/2)
        results = rank(SAMPLE_INDEX, ["world"], ["http://a.com"])
        assert results[0][1] == round(1 * expected_idf, 4)
