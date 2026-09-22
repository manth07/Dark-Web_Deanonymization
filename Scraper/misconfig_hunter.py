"""
Misconfiguration Hunter for Dark Web Threat Intelligence Platform.

Detects common server misconfigurations on .onion services and generates
search engine queries for SSL certificate pivoting.
"""

import hashlib
import logging
from typing import List

import requests

from tor_manager import TorManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MisconfigHunter:
    """Detects exposed paths and generates pivot queries for SSL certificates."""

    COMMON_EXPOSED_PATHS = [
        "/server-status",
        "/.git/config",
        "/phpinfo.php",
        "/info.php",
        "/test.php",
    ]

    def __init__(self, tor_manager: TorManager) -> None:
        """
        Initialize hunter with a TorManager instance.

        Args:
            tor_manager: Configured TorManager for session handling.
        """
        self.tor_manager = tor_manager
        logger.info("MisconfigHunter initialized")

    def check_exposed_paths(self, base_url: str) -> List[str]:
        """
        Probe common leakage paths on a .onion service.

        Args:
            base_url: Base .onion URL (e.g., http://example.onion).

        Returns:
            List of full URLs that returned HTTP 200 OK.
        """
        if not base_url.endswith("/"):
            base_url += "/"

        session = self.tor_manager.get_session()
        exposed = []

        for path in self.COMMON_EXPOSED_PATHS:
            test_url = f"{base_url}{path.lstrip('/')}"
            try:
                logger.info("Probing %s", test_url)
                response = session.get(test_url, timeout=15, allow_redirects=False)

                if response.status_code == 200:
                    logger.warning("EXPOSED: %s (status: %d)", test_url, response.status_code)
                    exposed.append(test_url)
                else:
                    logger.debug("Not exposed: %s (status: %d)", test_url, response.status_code)

            except requests.exceptions.Timeout:
                logger.warning("Timeout probing %s", test_url)
            except requests.exceptions.RequestException as e:
                logger.debug("Error probing %s: %s", test_url, e)

        if exposed:
            logger.info("Found %d exposed path(s) on %s", len(exposed), base_url)
        else:
            logger.info("No exposed paths found on %s", base_url)

        return exposed

    @staticmethod
    def generate_shodan_query(ssl_sha256_fingerprint: str) -> str:
        """
        Generate Shodan search dork for SSL certificate fingerprint.

        Args:
            ssl_sha256_fingerprint: Raw SHA-256 fingerprint (hex string, colons optional).

        Returns:
            Formatted Shodan query string.
        """
        clean_fp = ssl_sha256_fingerprint.replace(":", "").lower()
        return f'ssl.cert.fingerprint:"{clean_fp}"'

    @staticmethod
    def generate_censys_query(ssl_sha256_fingerprint: str) -> str:
        """
        Generate Censys search query for SSL certificate fingerprint.

        Args:
            ssl_sha256_fingerprint: Raw SHA-256 fingerprint (hex string, colons optional).

        Returns:
            Formatted Censys query string.
        """
        clean_fp = ssl_sha256_fingerprint.replace(":", "").lower()
        return f'services.tls.certificates.leaf_data.fingerprint.sha256:"{clean_fp}"'


if __name__ == "__main__":
    print("=" * 60)
    print("MisconfigHunter Standalone Test")
    print("=" * 60)

    tor_manager = TorManager()
    hunter = MisconfigHunter(tor_manager)

    test_onion = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"

    print(f"\n[1] Checking exposed paths on: {test_onion}")
    exposed = hunter.check_exposed_paths(test_onion)

    if exposed:
        print("    Exposed paths found:")
        for url in exposed:
            print(f"      - {url}")
    else:
        print("    No exposed paths detected.")

    print("\n[2] Testing query generators...")
    dummy_fp = "A1B2C3D4E5F67890A1B2C3D4E5F67890A1B2C3D4E5F67890A1B2C3D4E5F67890"

    shodan_query = MisconfigHunter.generate_shodan_query(dummy_fp)
    censys_query = MisconfigHunter.generate_censys_query(dummy_fp)

    print(f"    Shodan dork:  {shodan_query}")
    print(f"    Censys dork:  {censys_query}")

    print("\n[3] Testing with colon-formatted fingerprint...")
    colon_fp = "A1:B2:C3:D4:E5:F6:78:90:A1:B2:C3:D4:E5:F6:78:90:A1:B2:C3:D4:E5:F6:78:90:A1:B2:C3:D4:E5:F6"
    shodan_colon = MisconfigHunter.generate_shodan_query(colon_fp)
    censys_colon = MisconfigHunter.generate_censys_query(colon_fp)
    print(f"    Shodan dork:  {shodan_colon}")
    print(f"    Censys dork:  {censys_colon}")

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)