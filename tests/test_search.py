"""
Tests for the search module: AND queries and phrase queries.
"""

from search import and_query, phrase_query, has_consecutive_positions


# shared test index used across multiple tests
SAMPLE_INDEX = {
    "the": {
        "http://a.com": {"frequency": 2, "positions": [0, 3]},
        "http://b.com": {"frequency": 1, "positions": [0]}
    },
    "world": {
        "http://a.com": {"frequency": 1, "positions": [1]},
        "http://b.com": {"frequency": 1, "positions": [2]}
    },
    "is": {
        "http://a.com": {"frequency": 1, "positions": [2]}
    },
    "beautiful": {
        "http://a.com": {"frequency": 1, "positions": [4]}
    },
    "hello": {
        "http://b.com": {"frequency": 1, "positions": [1]}
    }
}
# http://a.com text: "the world is the beautiful" (positions 0-4)
# http://b.com text: "the hello world" (positions 0-2)


class TestAndQuery:
    """Tests for the and_query function."""

    def test_single_term(self):
        """A single term should return all URLs containing it."""
        results = and_query(SAMPLE_INDEX, ["the"])
        assert set(results) == {"http://a.com", "http://b.com"}

    def test_two_terms_both_present(self):
        """Two terms present in both docs should return both."""
        results = and_query(SAMPLE_INDEX, ["the", "world"])
        assert set(results) == {"http://a.com", "http://b.com"}

    def test_two_terms_one_doc(self):
        """Two terms only in one doc should return just that doc."""
        results = and_query(SAMPLE_INDEX, ["world", "is"])
        assert results == ["http://a.com"]

    def test_missing_term(self):
        """A query containing a term not in the index should return empty."""
        results = and_query(SAMPLE_INDEX, ["the", "nonexistent"])
        assert results == []

    def test_empty_terms(self):
        """An empty terms list should return empty."""
        results = and_query(SAMPLE_INDEX, [])
        assert results == []

    def test_term_in_no_docs(self):
        """A term not in the index at all should return empty."""
        results = and_query(SAMPLE_INDEX, ["zzzzz"])
        assert results == []


class TestPhraseQuery:
    """Tests for the phrase_query function."""

    def test_phrase_found(self):
        """'the world' is consecutive in http://a.com at positions 0,1."""
        results = phrase_query(SAMPLE_INDEX, ["the", "world"])
        assert "http://a.com" in results

    def test_phrase_not_consecutive(self):
        """'the beautiful' has positions 0/3 and 4, not consecutive."""
        results = phrase_query(SAMPLE_INDEX, ["the", "beautiful"])
        # "the" is at [0,3], "beautiful" is at [4]
        # 3+1 = 4, so "the beautiful" IS consecutive starting at position 3
        assert "http://a.com" in results

    def test_phrase_not_found(self):
        """'world the' should not be consecutive (reversed order)."""
        results = phrase_query(SAMPLE_INDEX, ["world", "the"])
        # "world" is at [1] in a.com, "the" is at [0,3]
        # need world at N and the at N+1: 1+1=2, but "the" is at [0,3], not 2
        # in b.com: "world" at [2], "the" at [0], 2+1=3, "the" not at 3
        assert results == []

    def test_single_term_phrase(self):
        """A single-term phrase should behave like an AND query."""
        results = phrase_query(SAMPLE_INDEX, ["the"])
        assert set(results) == {"http://a.com", "http://b.com"}

    def test_empty_phrase(self):
        """An empty phrase should return empty."""
        results = phrase_query(SAMPLE_INDEX, [])
        assert results == []

    def test_phrase_b_com(self):
        """'hello world' should be found in http://b.com at positions 1,2."""
        results = phrase_query(SAMPLE_INDEX, ["hello", "world"])
        assert results == ["http://b.com"]

    def test_phrase_missing_term(self):
        """A phrase with a missing term should return empty."""
        results = phrase_query(SAMPLE_INDEX, ["the", "missing"])
        assert results == []


class TestHasConsecutivePositions:
    """Tests for the has_consecutive_positions helper."""

    def test_simple_consecutive(self):
        """Positions [1] and [2] are consecutive."""
        assert has_consecutive_positions([[1], [2]]) is True

    def test_not_consecutive(self):
        """Positions [1] and [5] are not consecutive."""
        assert has_consecutive_positions([[1], [5]]) is False

    def test_multiple_options(self):
        """Should find a match among multiple positions."""
        assert has_consecutive_positions([[1, 5], [2, 8]]) is True

    def test_three_terms(self):
        """Three consecutive positions should match."""
        assert has_consecutive_positions([[0], [1], [2]]) is True

    def test_three_terms_gap(self):
        """Three terms with a gap should not match."""
        assert has_consecutive_positions([[0], [1], [5]]) is False

    def test_empty_list(self):
        """Empty input should return False."""
        assert has_consecutive_positions([]) is False
