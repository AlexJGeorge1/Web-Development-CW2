"""
Crawler module: fetches pages from quotes.toscrape.com using BFS.

Extracts quote text and author names from each page, follows pagination
links, and respects a configurable politeness delay between requests.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def crawl(start_url: str, max_pages: int = 50, delay: float = 6.0) -> dict[str, str]:
    """
    Crawl pages starting from start_url using breadth-first traversal.

    Args:
        start_url: the URL to begin crawling from.
        max_pages: maximum number of pages to fetch (default 50).
        delay: seconds to wait between requests (default 6.0).

    Returns:
        A dict mapping each visited URL to its extracted text content.
        Example: {"https://quotes.toscrape.com/page/1/": "quote text here..."}
    """
    visited = set()
    queue = [start_url]
    pages = {}

    while queue and len(pages) < max_pages:
        url = queue.pop(0)

        # skip pages we have already visited
        if url in visited:
            continue
        visited.add(url)

        # fetch the page, handle network errors gracefully
        try:
            print(f"Fetching: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue

        # parse the HTML and extract content
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = extract_text(soup)

        if page_text.strip():
            pages[url] = page_text

        # find the next page link and add it to the queue
        next_link = soup.select_one("li.next a")
        if next_link and next_link.get("href"):
            next_url = urljoin(url, next_link["href"])
            if next_url not in visited:
                queue.append(next_url)

        # respect the politeness delay before the next request
        if queue and len(pages) < max_pages:
            time.sleep(delay)

    print(f"Crawl complete. Fetched {len(pages)} pages.")
    return pages


def extract_text(soup: BeautifulSoup) -> str:
    """
    Extract readable text from a parsed HTML page.

    Pulls the text content from each quote block on the page,
    combining the quote itself and the author name.

    Args:
        soup: a BeautifulSoup object of the parsed page.

    Returns:
        A single string with all quote and author text from the page.
    """
    parts = []

    for quote_div in soup.select("div.quote"):
        # get the quote text (inside span.text)
        text_span = quote_div.select_one("span.text")
        if text_span:
            # strip the unicode quotation marks that the site uses
            quote_text = text_span.get_text(strip=True)
            quote_text = quote_text.strip("\u201c\u201d")
            parts.append(quote_text)

        # get the author name
        author_tag = quote_div.select_one("small.author")
        if author_tag:
            parts.append(author_tag.get_text(strip=True))

    return " ".join(parts)
