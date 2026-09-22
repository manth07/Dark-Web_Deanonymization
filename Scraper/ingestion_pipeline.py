"""
Ingestion Pipeline for Dark Web Threat Intelligence Platform.

Orchestrates the full collection workflow: Tor connection, scraping,
intelligence extraction, and misconfiguration hunting.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from extractor import IntelligenceExtractor
from misconfig_hunter import MisconfigHunter
from onion_scraper import OnionScraper
from tor_manager import TorManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Master orchestration pipeline for dark web ingestion."""

    def __init__(self) -> None:
        """Initialize all pipeline components."""
        logger.info("Initializing IngestionPipeline components...")

        self.tor_manager = TorManager()
        self.scraper = OnionScraper(self.tor_manager)
        self.extractor = IntelligenceExtractor()
        self.hunter = MisconfigHunter(self.tor_manager)

        logger.info("All components initialized successfully")

    def run_pipeline(self, target_url: str) -> dict[str, Any]:
        """
        Execute the full ingestion pipeline on a target .onion URL.

        Args:
            target_url: The .onion URL to ingest.

        Returns:
            Master dictionary with all collected intelligence.
        """
        logger.info("Starting pipeline for target: %s", target_url)
        timestamp = datetime.now(timezone.utc).isoformat()

        html_content = self.scraper.fetch_page(target_url)

        if not html_content:
            logger.error("Failed to fetch content from %s", target_url)
            return {
                "target_url": target_url,
                "timestamp": timestamp,
                "cache_file_path": None,
                "extracted_intelligence": {
                    "pgp_keys": [],
                    "btc_addresses": [],
                    "xmr_addresses": [],
                },
                "misconfigurations": {
                    "exposed_paths": [],
                },
                "error": "Failed to fetch page content",
            }

        cache_path = self.scraper.cache_page(html_content, self._sanitize_filename(target_url))
        logger.info("HTML cached to: %s", cache_path)

        extracted_intel = self.extractor.parse_document(html_content)
        logger.info(
            "Extracted intelligence: %d PGP keys, %d BTC, %d XMR",
            len(extracted_intel["pgp_keys"]),
            len(extracted_intel["btc_addresses"]),
            len(extracted_intel["xmr_addresses"]),
        )

        exposed_paths = self.hunter.check_exposed_paths(target_url)
        logger.info("Misconfiguration scan complete: %d exposed paths", len(exposed_paths))

        result = {
            "target_url": target_url,
            "timestamp": timestamp,
            "cache_file_path": cache_path,
            "extracted_intelligence": extracted_intel,
            "misconfigurations": {
                "exposed_paths": exposed_paths,
            },
        }

        logger.info("Pipeline completed successfully for %s", target_url)
        return result

    def export_to_json(self, data: dict[str, Any], output_filename: str = "scraped_data.json") -> None:
        """
        Export pipeline results to JSON file.

        Args:
            data: Master dictionary from run_pipeline().
            output_filename: Output file path (default: scraped_data.json).
        """
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        file_size = os.path.getsize(output_filename)
        logger.info("Results exported to %s (%d bytes)", output_filename, file_size)

    @staticmethod
    def _sanitize_filename(url: str) -> str:
        """
        Create a safe filename from a URL.

        Args:
            url: The URL to sanitize.

        Returns:
            Safe filename string.
        """
        prefix = url.replace("http://", "").replace("https://", "")
        safe = "".join(c for c in prefix if c.isalnum() or c in ("-", "_", "."))
        return safe[:50]


if __name__ == "__main__":
    print("=" * 60)
    print("IngestionPipeline Standalone Test")
    print("=" * 60)

    pipeline = IngestionPipeline()

    target = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"

    print(f"\n[1] Running pipeline against: {target}")
    result = pipeline.run_pipeline(target)

    print(f"\n[2] Exporting results to scraped_data.json...")
    pipeline.export_to_json(result)

    print("\n[3] Pipeline Summary:")
    print(f"    Target URL:     {result['target_url']}")
    print(f"    Timestamp:      {result['timestamp']}")
    print(f"    Cache File:     {result['cache_file_path']}")
    print(f"    PGP Keys:       {len(result['extracted_intelligence']['pgp_keys'])}")
    print(f"    BTC Addresses:  {len(result['extracted_intelligence']['btc_addresses'])}")
    print(f"    XMR Addresses:  {len(result['extracted_intelligence']['xmr_addresses'])}")
    print(f"    Exposed Paths:  {len(result['misconfigurations']['exposed_paths'])}")

    if result.get("error"):
        print(f"    Error:          {result['error']}")

    print("\n" + "=" * 60)
    print("Pipeline test completed - check scraped_data.json")
    print("=" * 60)