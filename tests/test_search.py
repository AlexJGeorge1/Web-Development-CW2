"""
Tests for the search module: AND queries and phrase queries.
"""

from search import and_query, phrase_query, has_consecutive_positions, edit_distance, suggest_terms


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


class TestEditDistance:
    """Tests for the edit_distance function."""

    def test_identical_strings(self):
        """Identical strings should have distance 0."""
        assert edit_distance("hello", "hello") == 0

    def test_single_insertion(self):
        """One character difference by insertion."""
        assert edit_distance("cat", "cats") == 1

    def test_single_deletion(self):
        """One character difference by deletion."""
        assert edit_distance("cats", "cat") == 1

    def test_single_substitution(self):
        """One character difference by substitution."""
        assert edit_distance("cat", "car") == 1

    def test_completely_different(self):
        """Completely different strings of same length."""
        assert edit_distance("abc", "xyz") == 3

    def test_empty_strings(self):
        """Two empty strings should have distance 0."""
        assert edit_distance("", "") == 0

    def test_one_empty(self):
        """Distance from empty to a string is the string length."""
        assert edit_distance("", "hello") == 5
        assert edit_distance("hello", "") == 5

    def test_transposition(self):
        """Swapping two adjacent characters costs 2 edits."""
        assert edit_distance("ab", "ba") == 2

    def test_longer_example(self):
        """A known edit distance between two words."""
        assert edit_distance("kitten", "sitting") == 3


class TestSuggestTerms:
    """Tests for the suggest_terms function."""

    def test_suggests_close_match(self):
        """Should suggest 'world' when given 'worl'."""
        suggestions = suggest_terms(SAMPLE_INDEX, "worl")
        assert "world" in suggestions

    def test_suggests_by_substitution(self):
        """Should suggest 'hello' when given 'hallo'."""
        suggestions = suggest_terms(SAMPLE_INDEX, "hallo")
        assert "hello" in suggestions

    def test_no_exact_match_in_suggestions(self):
        """An exact match (distance 0) should not appear in suggestions."""
        suggestions = suggest_terms(SAMPLE_INDEX, "the")
        assert "the" not in suggestions

    def test_empty_term(self):
        """An empty term should return no suggestions."""
        assert suggest_terms(SAMPLE_INDEX, "") == []

    def test_empty_index(self):
        """An empty index should return no suggestions."""
        assert suggest_terms({}, "hello") == []

    def test_max_suggestions_limit(self):
        """Should not return more than max_suggestions."""
        suggestions = suggest_terms(SAMPLE_INDEX, "th", max_suggestions=2)
        assert len(suggestions) <= 2

    def test_sorted_by_distance(self):
        """Closer matches should appear before distant ones."""
        suggestions = suggest_terms(SAMPLE_INDEX, "worl")
        if len(suggestions) > 1:
            d0 = edit_distance("worl", suggestions[0])
            d1 = edit_distance("worl", suggestions[1])
            assert d0 <= d1

    def test_very_different_term(self):
        """A term very different from anything in the index returns empty."""
        suggestions = suggest_terms(SAMPLE_INDEX, "zzzzzzzzzzz")
        assert suggestions == []
