"""
Tests for the crawler module.

These tests use unittest.mock to avoid hitting the live website.
We mock requests.get to return fake HTML responses so we can test
the crawling logic and text extraction in isolation.
"""

from unittest.mock import patch, MagicMock

from crawler import crawl, extract_text
from bs4 import BeautifulSoup


def make_mock_response(html: str, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response with the given HTML."""
    mock = MagicMock()
    mock.text = html
    mock.status_code = status_code
    mock.raise_for_status = MagicMock()
    return mock


# sample HTML that mimics the structure of quotes.toscrape.com
SAMPLE_PAGE_1 = """
<html>
<body>
<div class="quote">
    <span class="text">\u201cThe world is beautiful.\u201d</span>
    <small class="author">Author One</small>
</div>
<div class="quote">
    <span class="text">\u201cLife is good.\u201d</span>
    <small class="author">Author Two</small>
</div>
<nav>
    <ul class="pager">
        <li class="next"><a href="/page/2/">Next</a></li>
    </ul>
</nav>
</body>
</html>
"""

SAMPLE_PAGE_2 = """
<html>
<body>
<div class="quote">
    <span class="text">\u201cKnowledge is power.\u201d</span>
    <small class="author">Author Three</small>
</div>
</body>
</html>
"""


class TestExtractText:
    """Tests for the extract_text helper."""

    def test_extracts_quotes_and_authors(self):
        """Should extract quote text and author names."""
        soup = BeautifulSoup(SAMPLE_PAGE_1, "html.parser")
        text = extract_text(soup)

        assert "The world is beautiful." in text
        assert "Author One" in text
        assert "Life is good." in text
        assert "Author Two" in text

    def test_strips_unicode_quotes(self):
        """Unicode quotation marks should be stripped from quote text."""
        soup = BeautifulSoup(SAMPLE_PAGE_1, "html.parser")
        text = extract_text(soup)

        # the curly quotes should be removed
        assert "\u201c" not in text
        assert "\u201d" not in text

    def test_empty_page(self):
        """A page with no quote divs should return empty string."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        text = extract_text(soup)
        assert text.strip() == ""

    def test_missing_author(self):
        """A quote div without an author tag should still extract the quote."""
        html = """
        <div class="quote">
            <span class="text">\u201cSome quote.\u201d</span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        text = extract_text(soup)
        assert "Some quote." in text


class TestCrawl:
    """Tests for the crawl function using mocked HTTP responses."""

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_single_page(self, mock_sleep, mock_get):
        """Crawling with max_pages=1 should fetch one page."""
        mock_get.return_value = make_mock_response(SAMPLE_PAGE_2)

        pages = crawl("http://test.com", max_pages=1)

        assert len(pages) == 1
        assert "http://test.com" in pages
        assert "Knowledge is power." in pages["http://test.com"]

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_follows_pagination(self, mock_sleep, mock_get):
        """Crawler should follow the next page link."""
        # first call returns page 1 (with next link), second returns page 2
        mock_get.side_effect = [
            make_mock_response(SAMPLE_PAGE_1),
            make_mock_response(SAMPLE_PAGE_2)
        ]

        pages = crawl("http://test.com", max_pages=2)

        assert len(pages) == 2
        assert mock_get.call_count == 2

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_respects_max_pages(self, mock_sleep, mock_get):
        """Crawler should stop after reaching max_pages."""
        mock_get.return_value = make_mock_response(SAMPLE_PAGE_1)

        pages = crawl("http://test.com", max_pages=1)

        assert len(pages) == 1
        # should only make one request despite there being a next link
        assert mock_get.call_count == 1

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_handles_network_error(self, mock_sleep, mock_get):
        """Network errors should be caught and the page skipped."""
        import requests as req
        mock_get.side_effect = req.RequestException("Connection failed")

        pages = crawl("http://test.com", max_pages=1)

        assert len(pages) == 0

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_calls_sleep(self, mock_sleep, mock_get):
        """The politeness delay should be called between requests."""
        mock_get.side_effect = [
            make_mock_response(SAMPLE_PAGE_1),
            make_mock_response(SAMPLE_PAGE_2)
        ]

        crawl("http://test.com", max_pages=2, delay=6.0)

        # sleep should be called at least once (between the two requests)
        mock_sleep.assert_called_with(6.0)

    @patch("crawler.requests.get")
    @patch("crawler.time.sleep")
    def test_crawl_no_duplicate_visits(self, mock_sleep, mock_get):
        """The crawler should not visit the same URL twice."""
        # page links back to itself using the same full URL
        circular_html = """
        <html><body>
        <div class="quote">
            <span class="text">\u201cCircular.\u201d</span>
            <small class="author">Author</small>
        </div>
        <nav><ul class="pager">
            <li class="next"><a href="http://test.com/page/1/">Next</a></li>
        </ul></nav>
        </body></html>
        """
        mock_get.return_value = make_mock_response(circular_html)

        pages = crawl("http://test.com/page/1/", max_pages=5)

        # should only visit once since the next link points to the same URL
        assert mock_get.call_count == 1
