"""
Tor Connection Manager for Dark Web Threat Intelligence Platform.

Provides session management, circuit rotation, and connection verification
for secure Tor network communications.
"""

import logging
import os
import time
from typing import Any

import requests
from dotenv import load_dotenv
from stem import Signal, SocketError
from stem.connection import AuthenticationFailure
from stem.control import Controller

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TorManager:
    """Manages Tor connections, sessions, and circuit rotation."""

    def __init__(
        self,
        socks_port: int | None = None,
        control_port: int | None = None,
        control_password: str | None = None,
    ) -> None:
        """
        Initialize TorManager with configuration.

        Args:
            socks_port: SOCKS proxy port (default: 9050 or SOCKS_PORT env)
            control_port: Control port for circuit management (default: 9051 or CONTROL_PORT env)
            control_password: Control port password (default: TOR_PASSWORD env or None)
        """
        self.socks_port = socks_port or int(os.getenv("SOCKS_PORT", "9050"))
        self.control_port = control_port or int(os.getenv("CONTROL_PORT", "9051"))
        self.control_password = control_password or os.getenv("TOR_PASSWORD", "") or None

        self._session: requests.Session | None = None

        logger.info(
            "TorManager initialized: socks_port=%d, control_port=%d, password_configured=%s",
            self.socks_port,
            self.control_port,
            bool(self.control_password),
        )

    def get_session(self) -> requests.Session:
        """
        Create and return a requests.Session routed through Tor SOCKS5h proxy.

        Uses socks5h:// to ensure DNS resolution occurs over Tor circuit,
        preventing local DNS leaks.

        Returns:
            Configured requests.Session with Tor proxy and realistic User-Agent.
        """
        if self._session is not None:
            return self._session

        proxy_url = f"socks5h://127.0.0.1:{self.socks_port}"

        session = requests.Session()
        session.proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) "
                    "Gecko/20100101 Firefox/115.0"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        self._session = session
        logger.info("Tor session created with proxy: %s", proxy_url)
        return session

    def renew_circuit(self) -> bool:
        """
        Request a new Tor circuit (NEWNYM signal) via control port.

        Authenticates using password if provided, otherwise uses cookie authentication.
        Waits for circuit to stabilize before returning.

        Returns:
            True if circuit renewal succeeded, False otherwise.
        """
        try:
            logger.info("Connecting to Tor control port %d for circuit renewal", self.control_port)

            with Controller.from_port(port=self.control_port) as controller:
                if self.control_password:
                    logger.debug("Authenticating with password")
                    controller.authenticate(password=self.control_password)
                else:
                    logger.debug("Authenticating with cookie")
                    controller.authenticate()

                logger.info("Sending NEWNYM signal")
                controller.signal(Signal.NEWNYM)

                wait_time = controller.get_newnym_wait()
                logger.info("Waiting %d seconds for new circuit to build", wait_time)
                time.sleep(wait_time)

            logger.info("Circuit renewal completed successfully")
            return True

        except SocketError as e:
            logger.error("Failed to connect to Tor control port: %s", e)
            return False
        except AuthenticationFailure as e:
            logger.error("Tor control port authentication failed: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error during circuit renewal: %s", e)
            return False

    def verify_connection(self) -> dict[str, Any]:
        """
        Verify Tor connection by querying check.torproject.org.

        Returns:
            Dictionary with keys: is_tor (bool), ip (str), timestamp (str).

        Raises:
            requests.exceptions.RequestException: If connection fails.
            ValueError: If response indicates non-Tor connection.
        """
        session = self.get_session()
        url = "https://check.torproject.org/api/ip"

        try:
            logger.info("Verifying Tor connection via %s", url)
            response = session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            is_tor = data.get("IsTor", False)
            ip = data.get("IP", "unknown")
            timestamp = data.get("Timestamp", "")

            if not is_tor:
                logger.error("Connection verification failed: Not using Tor (IP: %s)", ip)
                raise ValueError(f"Connection is not routed through Tor. Exit IP: {ip}")

            logger.info("Tor connection verified: IP=%s, Timestamp=%s", ip, timestamp)
            return {"is_tor": is_tor, "ip": ip, "timestamp": timestamp}

        except requests.exceptions.RequestException as e:
            logger.error("Connection verification request failed: %s", e)
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error("Unexpected error during connection verification: %s", e)
            raise requests.exceptions.RequestException(f"Verification failed: {e}") from e


if __name__ == "__main__":
    print("=" * 60)
    print("TorManager Standalone Test")
    print("=" * 60)

    manager = TorManager()

    try:
        print("\n[1] Initial connection verification...")
        result = manager.verify_connection()
        print(f"    Exit IP: {result['ip']}")
        print(f"    Is Tor: {result['is_tor']}")
        print(f"    Timestamp: {result['timestamp']}")

        print("\n[2] Renewing circuit...")
        success = manager.renew_circuit()
        if success:
            print("    Circuit renewed successfully")
        else:
            print("    Circuit renewal failed")

        print("\n[3] Post-renewal verification...")
        result = manager.verify_connection()
        print(f"    Exit IP: {result['ip']}")
        print(f"    Is Tor: {result['is_tor']}")
        print(f"    Timestamp: {result['timestamp']}")

        print("\n" + "=" * 60)
        print("Test completed successfully")
        print("=" * 60)

    except ValueError as e:
        print(f"\n[ERROR] Tor verification failed: {e}")
        print("Ensure Tor service is running on the configured ports.")
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Connection error: {e}")
        print("Check Tor SOCKS proxy is accessible on port", manager.socks_port)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")