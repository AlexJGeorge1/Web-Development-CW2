"""
Tests for the CLI entry point (main.py).

Tests the command routing, output formatting, and error handling
of the CLI without hitting the live site or real filesystem.
"""

import json
import os
from unittest.mock import patch, MagicMock

import pytest

from main import main, print_entry, handle_find


# a minimal index for CLI testing
MINI_INDEX = {
    "love": {
        "http://a.com": {"frequency": 3, "positions": [0, 5, 10]},
        "http://b.com": {"frequency": 1, "positions": [2]}
    },
    "life": {
        "http://a.com": {"frequency": 2, "positions": [1, 6]},
        "http://b.com": {"frequency": 1, "positions": [3]}
    },
    "is": {
        "http://a.com": {"frequency": 1, "positions": [2]}
    }
}


class TestPrintEntry:
    """Tests for the print_entry helper."""

    def test_prints_existing_word(self, capsys):
        """Should print the entry for a word that exists."""
        print_entry(MINI_INDEX, "love")
        output = capsys.readouterr().out
        assert "'love' found in 2 document(s)" in output
        assert "http://a.com" in output
        assert "Frequency: 3" in output

    def test_prints_not_found(self, capsys):
        """Should print a message for a word not in the index."""
        print_entry(MINI_INDEX, "xyz")
        output = capsys.readouterr().out
        assert "'xyz' not found in the index" in output

    def test_case_insensitive_lookup(self, capsys):
        """Lookup should be case-insensitive."""
        print_entry(MINI_INDEX, "LOVE")
        output = capsys.readouterr().out
        assert "'love' found in 2 document(s)" in output


class TestHandleFind:
    """Tests for the handle_find function."""

    def test_and_query_results(self, capsys):
        """An AND query should return matching URLs."""
        handle_find(MINI_INDEX, ["love", "life"])
        output = capsys.readouterr().out
        assert "AND query" in output
        assert "http://a.com" in output

    def test_phrase_query_detected(self, capsys):
        """A quoted query should be treated as a phrase query."""
        handle_find(MINI_INDEX, ['"love', 'life"'])
        output = capsys.readouterr().out
        assert "Phrase query" in output

    def test_no_results(self, capsys):
        """A query with no matches should say so."""
        handle_find(MINI_INDEX, ["nonexistent"])
        output = capsys.readouterr().out
        assert "No results found" in output

    def test_results_show_scores(self, capsys):
        """Results should include TF-IDF scores."""
        handle_find(MINI_INDEX, ["love"])
        output = capsys.readouterr().out
        assert "Score:" in output


class TestMainCLI:
    """Tests for the main() entry point with mocked sys.argv."""

    @patch("main.sys")
    def test_no_args_prints_usage(self, mock_sys, capsys):
        """Running with no arguments should print usage."""
        mock_sys.argv = ["main.py"]
        main()
        output = capsys.readouterr().out
        assert "Usage:" in output or "Search Engine CLI" in output

    @patch("main.sys")
    def test_unknown_command(self, mock_sys, capsys):
        """An unknown command should print an error and usage."""
        mock_sys.argv = ["main.py", "badcommand"]
        main()
        output = capsys.readouterr().out
        assert "Unknown command" in output

    @patch("main.crawl")
    @patch("main.build_index")
    @patch("main.save_index")
    @patch("main.sys")
    def test_build_command(self, mock_sys, mock_save, mock_build, mock_crawl, capsys):
        """The build command should crawl, build index, and save."""
        mock_sys.argv = ["main.py", "build"]
        mock_crawl.return_value = {"http://test.com": "hello world"}
        mock_build.return_value = {"hello": {"http://test.com": {"frequency": 1, "positions": [0]}}}

        main()

        mock_crawl.assert_called_once()
        mock_build.assert_called_once()
        mock_save.assert_called_once()

    @patch("main.load_index")
    @patch("main.sys")
    def test_load_command(self, mock_sys, mock_load, capsys):
        """The load command should call load_index."""
        mock_sys.argv = ["main.py", "load"]
        mock_load.return_value = {"hello": {}}

        main()

        mock_load.assert_called_once()
        output = capsys.readouterr().out
        assert "loaded" in output.lower()

    @patch("main.load_index")
    @patch("main.sys")
    def test_print_command(self, mock_sys, mock_load, capsys):
        """The print command should load index and print the entry."""
        mock_sys.argv = ["main.py", "print", "love"]
        mock_load.return_value = MINI_INDEX

        main()

        mock_load.assert_called_once()
        output = capsys.readouterr().out
        assert "love" in output

    @patch("main.load_index")
    @patch("main.sys")
    def test_find_command(self, mock_sys, mock_load, capsys):
        """The find command should load index and run a search."""
        mock_sys.argv = ["main.py", "find", "love"]
        mock_load.return_value = MINI_INDEX

        main()

        mock_load.assert_called_once()
        output = capsys.readouterr().out
        assert "result" in output.lower()

    @patch("main.sys")
    def test_print_no_word(self, mock_sys, capsys):
        """Print without a word argument should show usage."""
        mock_sys.argv = ["main.py", "print"]
        main()
        output = capsys.readouterr().out
        assert "Usage:" in output or "print" in output.lower()

    @patch("main.sys")
    def test_find_no_query(self, mock_sys, capsys):
        """Find without a query should show usage."""
        mock_sys.argv = ["main.py", "find"]
        main()
        output = capsys.readouterr().out
        assert "Usage:" in output or "find" in output.lower()
