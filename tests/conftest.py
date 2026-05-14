"""
Shared test fixtures and configuration.

The pythonpath setting in pyproject.toml handles imports,
so we do not need sys.path hacks in individual test files.
"""

import pytest
from indexer import build_index


@pytest.fixture
def sample_pages():
    """A small set of pages for integration-style tests."""
    return {
        "http://a.com": "the world is the beautiful place",
        "http://b.com": "the hello world of love",
        "http://c.com": "life is a journey of love and life"
    }


@pytest.fixture
def sample_index(sample_pages):
    """A pre-built index from sample_pages."""
    return build_index(sample_pages)
