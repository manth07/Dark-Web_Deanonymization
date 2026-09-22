"""
Robust Onion Scraper for Dark Web Threat Intelligence Platform.

Provides resilient fetching with retry logic, exponential backoff,
and HTML caching for .onion sites via Tor.
"""

import logging
import os
import time
from datetime import datetime , timezone
from typing import Optional

import requests

from tor_manager import TorManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class OnionScraper:
    """Resilient scraper for .onion sites with retry logic and caching."""

    def __init__(self, tor_manager: TorManager) -> None:
        """
        Initialize scraper with a TorManager instance.

        Args:
            tor_manager: Configured TorManager for session handling.
        """
        self.tor_manager = tor_manager
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info("OnionScraper initialized, cache directory: %s", self.cache_dir)

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch an .onion page with exponential backoff retries.

        Args:
            url: The .onion URL to fetch.
            max_retries: Maximum number of retry attempts (default: 3).

        Returns:
            Raw HTML text if successful, None if all retries exhausted.
        """
        session = self.tor_manager.get_session()
        timeout = 30

        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Fetching %s (attempt %d/%d)", url, attempt, max_retries)
                response = session.get(url, timeout=timeout)
                response.raise_for_status()

                logger.info("Successfully fetched %s (status: %d)", url, response.status_code)
                return response.text

            except requests.exceptions.Timeout:
                logger.warning("Timeout fetching %s (attempt %d/%d)", url, attempt, max_retries)
            except requests.exceptions.HTTPError as e:
                if 500 <= e.response.status_code < 600:
                    logger.warning(
                        "Server error %d for %s (attempt %d/%d)",
                        e.response.status_code,
                        url,
                        attempt,
                        max_retries,
                    )
                else:
                    logger.error("Client error %d for %s - not retrying", e.response.status_code, url)
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning("Request error for %s (attempt %d/%d): %s", url, attempt, max_retries, e)

            if attempt < max_retries:
                wait_time = 5 * (2 ** (attempt - 1))
                logger.info("Waiting %ds before retry...", wait_time)
                time.sleep(wait_time)

        logger.error("All %d retries exhausted for %s", max_retries, url)
        return None

    def cache_page(self, html_content: str, site_name: str) -> str:
        """
        Save HTML content to cache with timestamped filename.

        Args:
            html_content: Raw HTML to cache.
            site_name: Identifier for the site (used in filename).

        Returns:
            Path to the saved cache file.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in site_name if c.isalnum() or c in ("-", "_"))
        filename = f"{safe_name}_{timestamp}.html"
        filepath = os.path.join(self.cache_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Cached page to %s (%d bytes)", filepath, len(html_content))
        return filepath


if __name__ == "__main__":
    print("=" * 60)
    print("OnionScraper Standalone Test")
    print("=" * 60)

    tor_manager = TorManager()
    scraper = OnionScraper(tor_manager)

    test_url = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"
    site_name = "ahmia_test"

    print(f"\n[1] Scraping: {test_url}")
    html = scraper.fetch_page(test_url)

    if html:
        print(f"    Success: Received {len(html)} bytes")
        filepath = scraper.cache_page(html, site_name)
        print(f"[2] Cached to: {filepath}")
    else:
        print("    Failed: Could not fetch page after retries")
        print("    Ensure Tor is running and the .onion is accessible.")

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)