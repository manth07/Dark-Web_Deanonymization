"""High-precision extraction engine for cryptocurrency wallets, PGP keys, and IP indicators."""
import ipaddress
import re
from typing import List, Set
from schemas.extracted_features import CryptoWallet, ExtractedIdentifiers

# Cryptocurrency Address Regular Expressions
# Bitcoin (BTC)
BTC_P2PKH_REGEX = re.compile(r"\b(1[1-9A-HJ-NP-Za-km-z]{25,34})\b")
BTC_P2SH_REGEX = re.compile(r"\b(3[1-9A-HJ-NP-Za-km-z]{33})\b")
BTC_BECH32_REGEX = re.compile(r"\b(bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59})\b", re.IGNORECASE)

# Monero (XMR)
XMR_STANDARD_REGEX = re.compile(r"\b(4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})\b")
XMR_INTEGRATED_REGEX = re.compile(r"\b(8[0-9AB][1-9A-HJ-NP-Za-km-z]{104})\b")

# Ethereum (ETH)
ETH_REGEX = re.compile(r"\b(0x[a-fA-F0-9]{40})\b")

# PGP Keys & Fingerprints
PGP_BLOCK_REGEX = re.compile(
    r"(-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----)",
    re.MULTILINE,
)
PGP_FINGERPRINT_CONTIGUOUS = re.compile(r"(?<!0x)(?<![a-fA-F0-9])([0-9a-fA-F]{40})(?![a-fA-F0-9])")
PGP_FINGERPRINT_SPACED = re.compile(
    r"\b([0-9a-fA-F]{4}(?:\s+[0-9a-fA-F]{4}){9})\b"
)

# IPv4
IPV4_REGEX = re.compile(
    r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)


# Private / Loopback IPv4 subnets (RFC 1918, RFC 3927, RFC 1122)
PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]


class IdentifierExtractor:
    """Extracts cryptocurrency wallets, PGP key signatures, and IP indicators from raw text."""

    def __init__(self) -> None:
        pass

    def extract_crypto_wallets(self, text: str) -> List[CryptoWallet]:
        """Extract and categorize Bitcoin, Monero, and Ethereum cryptocurrency wallets."""
        if not text or not isinstance(text, str):
            return []

        wallets: List[CryptoWallet] = []
        seen: Set[str] = set()

        def add_wallet(curr: str, addr: str) -> None:
            if addr not in seen:
                seen.add(addr)
                wallets.append(CryptoWallet(currency=curr, address=addr))

        # 1. Monero (check first due to length)
        for match in XMR_STANDARD_REGEX.finditer(text):
            add_wallet("XMR", match.group(1))

        for match in XMR_INTEGRATED_REGEX.finditer(text):
            add_wallet("XMR", match.group(1))

        # 2. Ethereum (starts with 0x)
        for match in ETH_REGEX.finditer(text):
            add_wallet("ETH", match.group(1))

        # 3. Bitcoin: Bech32
        for match in BTC_BECH32_REGEX.finditer(text):
            add_wallet("BTC", match.group(1))

        # 4. Bitcoin: Legacy P2PKH (starts with 1)
        for match in BTC_P2PKH_REGEX.finditer(text):
            addr = match.group(1)
            add_wallet("BTC", addr)

        # 5. Bitcoin: P2SH (starts with 3)
        for match in BTC_P2SH_REGEX.finditer(text):
            add_wallet("BTC", match.group(1))

        return wallets

    def extract_pgp_keys(self, text: str) -> List[str]:
        """Extract ASCII-armored PGP key blocks and 40-character hexadecimal fingerprints."""
        if not text or not isinstance(text, str):
            return []

        pgp_items: List[str] = []
        seen: Set[str] = set()

        # 1. ASCII Armor Blocks
        for match in PGP_BLOCK_REGEX.finditer(text):
            block = match.group(1).strip()
            if block not in seen:
                seen.add(block)
                pgp_items.append(block)

        # 2. Spaced Fingerprints (e.g. "4A5B 6C7D ...")
        for match in PGP_FINGERPRINT_SPACED.finditer(text):
            fp_clean = re.sub(r"\s+", "", match.group(1)).upper()
            if fp_clean not in seen:
                seen.add(fp_clean)
                pgp_items.append(fp_clean)

        # 3. Contiguous Fingerprints (40 hex chars)
        for match in PGP_FINGERPRINT_CONTIGUOUS.finditer(text):
            fp = match.group(1).upper()
            if fp not in seen:
                seen.add(fp)
                pgp_items.append(fp)

        return pgp_items

    def extract_ip_addresses(self, text: str, include_private: bool = False) -> List[str]:
        """Extract IPv4 addresses, filtering private/loopback/reserved subnets unless specified."""
        if not text or not isinstance(text, str):
            return []

        valid_ips: List[str] = []
        seen: Set[str] = set()

        for match in IPV4_REGEX.finditer(text):
            ip_str = match.group(0)
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                if ip_obj.version != 4:
                    continue

                if not include_private:
                    is_filtered = (
                        any(ip_obj in net for net in PRIVATE_NETWORKS)
                        or ip_str == "255.255.255.255"
                        or ip_obj.is_multicast
                    )
                    if is_filtered:
                        continue

                if ip_str not in seen:
                    seen.add(ip_str)
                    valid_ips.append(ip_str)
            except ValueError:
                continue

        return valid_ips

    def extract_all(self, text: str, include_private_ips: bool = False) -> ExtractedIdentifiers:
        """Harvest all cryptocurrency wallets, PGP artifacts, and public IP indicators."""
        if not text or not isinstance(text, str):
            return ExtractedIdentifiers()

        wallets = self.extract_crypto_wallets(text)
        pgp_keys = self.extract_pgp_keys(text)
        ips = self.extract_ip_addresses(text, include_private=include_private_ips)

        return ExtractedIdentifiers(
            crypto_wallets=wallets,
            pgp_keys=pgp_keys,
            ip_addresses=ips,
        )
