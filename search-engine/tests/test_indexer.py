"""
Tests for the indexer module: tokenisation and index building.
"""

from indexer import tokenise, build_index


# -- tokenise tests --

class TestTokenise:
    """Tests for the tokenise function."""

    def test_basic_sentence(self):
        """Lowercase and split a simple sentence."""
        result = tokenise("Hello World")
        assert result == ["hello", "world"]

    def test_punctuation_removal(self):
        """Punctuation should be stripped from tokens."""
        result = tokenise("Hello, World! How's it going?")
        assert result == ["hello", "world", "hows", "it", "going"]

    def test_numbers_preserved(self):
        """Numbers should be kept as tokens."""
        result = tokenise("There are 42 cats")
        assert result == ["there", "are", "42", "cats"]

    def test_mixed_case(self):
        """Everything should be lowercased."""
        result = tokenise("UPPER lower MiXeD")
        assert result == ["upper", "lower", "mixed"]

    def test_empty_string(self):
        """An empty string should return an empty list."""
        result = tokenise("")
        assert result == []

    def test_whitespace_only(self):
        """A string of just whitespace should return empty list."""
        result = tokenise("   \t\n  ")
        assert result == []

    def test_special_characters_only(self):
        """A string of just special chars should return empty list."""
        result = tokenise("!@#$%^&*()")
        assert result == []

    def test_extra_whitespace(self):
        """Multiple spaces between words should not produce empty tokens."""
        result = tokenise("hello    world")
        assert result == ["hello", "world"]

    def test_unicode_quotes_stripped(self):
        """Smart quotes and similar unicode should be stripped."""
        result = tokenise("\u201cHello\u201d")
        assert result == ["hello"]


# -- build_index tests --

class TestBuildIndex:
    """Tests for the build_index function."""

    def test_single_page_single_word(self):
        """Index a single word from a single page."""
        pages = {"http://example.com": "hello"}
        index = build_index(pages)

        assert "hello" in index
        assert "http://example.com" in index["hello"]
        assert index["hello"]["http://example.com"]["frequency"] == 1
        assert index["hello"]["http://example.com"]["positions"] == [0]

    def test_repeated_word(self):
        """A word appearing multiple times should have correct frequency and positions."""
        pages = {"http://example.com": "the cat and the dog"}
        index = build_index(pages)

        assert index["the"]["http://example.com"]["frequency"] == 2
        assert index["the"]["http://example.com"]["positions"] == [0, 3]

    def test_multiple_pages(self):
        """Words should be indexed across multiple pages."""
        pages = {
            "http://a.com": "hello world",
            "http://b.com": "hello there"
        }
        index = build_index(pages)

        # "hello" appears in both pages
        assert len(index["hello"]) == 2
        assert "http://a.com" in index["hello"]
        assert "http://b.com" in index["hello"]

        # "world" only appears in one page
        assert len(index["world"]) == 1
        assert "http://a.com" in index["world"]

    def test_positions_are_correct(self):
        """Positions should match the zero-indexed token positions."""
        pages = {"http://example.com": "apple banana cherry"}
        index = build_index(pages)

        assert index["apple"]["http://example.com"]["positions"] == [0]
        assert index["banana"]["http://example.com"]["positions"] == [1]
        assert index["cherry"]["http://example.com"]["positions"] == [2]

    def test_empty_pages(self):
        """An empty pages dict should produce an empty index."""
        index = build_index({})
        assert index == {}

    def test_page_with_punctuation(self):
        """Punctuation in page text should be handled by tokeniser."""
        pages = {"http://example.com": "Hello, world!"}
        index = build_index(pages)

        assert "hello" in index
        assert "world" in index
        # the raw punctuated forms should not be in the index
        assert "Hello," not in index
        assert "world!" not in index

    def test_index_structure(self):
        """Verify the full structure of an index entry."""
        pages = {"http://example.com": "cat dog cat"}
        index = build_index(pages)

        cat_entry = index["cat"]["http://example.com"]
        assert "frequency" in cat_entry
        assert "positions" in cat_entry
        assert cat_entry["frequency"] == 2
        assert cat_entry["positions"] == [0, 2]
