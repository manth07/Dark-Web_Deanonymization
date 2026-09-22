"""
Intelligence Extractor for Dark Web Threat Intelligence Platform.

Extracts threat actor identifiers from unstructured text using robust regex patterns.
"""

import json
import re


class IntelligenceExtractor:
    """Extracts cryptocurrency addresses and PGP keys from text."""

    PGP_PUBLIC_KEY_PATTERN = re.compile(
        r"-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----",
        re.MULTILINE,
    )

    BTC_LEGACY_PATTERN = re.compile(
        r"\b[1][a-km-zA-HJ-NP-Z1-9]{25,34}\b"
    )
    BTC_P2SH_PATTERN = re.compile(
        r"\b[3][a-km-zA-HJ-NP-Z1-9]{25,34}\b"
    )
    BTC_SEGWIT_PATTERN = re.compile(
        r"\bbc1[a-zA-HJ-NP-Z0-9]{39,59}\b"
    )

    XMR_PATTERN = re.compile(
        r"\b[48][a-km-zA-HJ-NP-Z1-9]{94}\b"
    )

    @classmethod
    def extract_pgp_keys(cls, text: str) -> list[str]:
        """
        Extract PGP Public Key blocks from text.

        Args:
            text: Input text to search.

        Returns:
            List of PGP Public Key blocks found.
        """
        matches = cls.PGP_PUBLIC_KEY_PATTERN.findall(text)
        return [match.strip() for match in matches]

    @classmethod
    def extract_btc_addresses(cls, text: str) -> list[str]:
        """
        Extract Bitcoin addresses from text.

        Supports:
        - Legacy (P2PKH): starts with '1', 26-35 chars
        - Pay-to-Script-Hash (P2SH): starts with '3', 26-35 chars
        - SegWit (Bech32): starts with 'bc1', 42-62 chars

        Args:
            text: Input text to search.

        Returns:
            List of unique Bitcoin addresses found.
        """
        addresses = set()

        for pattern in (
            cls.BTC_LEGACY_PATTERN,
            cls.BTC_P2SH_PATTERN,
            cls.BTC_SEGWIT_PATTERN,
        ):
            matches = pattern.findall(text)
            addresses.update(matches)

        return sorted(addresses)

    @classmethod
    def extract_xmr_addresses(cls, text: str) -> list[str]:
        """
        Extract Monero addresses from text.

        Monero addresses:
        - Start with '4' (mainnet) or '8' (subaddress/integrated)
        - Exactly 95 alphanumeric characters (base58)
        - Use same alphabet as Bitcoin (no 0, O, I, l)

        Args:
            text: Input text to search.

        Returns:
            List of unique Monero addresses found.
        """
        matches = cls.XMR_PATTERN.findall(text)
        return sorted(set(matches))

    @classmethod
    def parse_document(cls, text: str) -> dict[str, list[str]]:
        """
        Run all extraction methods on the provided text.

        Args:
            text: Input text to analyze.

        Returns:
            Structured dictionary with all extracted indicators.
        """
        return {
            "pgp_keys": cls.extract_pgp_keys(text),
            "btc_addresses": cls.extract_btc_addresses(text),
            "xmr_addresses": cls.extract_xmr_addresses(text),
        }


if __name__ == "__main__":
    mock_forum_post = """
    ============================================================
    [VENDOR] Premium Credit Cards & Fullz - Escrow Accepted
    ============================================================

    Hello buyers,

    Fresh batch of high-balance CCs with CVV2, billing ZIP, and DOB.
    All cards tested and verified working on major gateways.

    Price List:
    - US Gold/Platinum: $45 each (min 5)
    - EU Corporate: $60 each (min 3)
    - Fullz packs (SSN + DL + BG): $25 each

    Payment: BTC or XMR only. Escrow via market supported.

    My BTC wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
    My XMR wallet: 44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otXft3XjrpDtQGv7SqSsaBYBb98uNbr2VBBEt7f2wfn3RVGQBEP3A

    --- VERIFICATION ---
    Here is my PGP key for signed comms:

-----BEGIN PGP PUBLIC KEY BLOCK-----
    mQINBF8z9nIBEADJgQJ0Q8zL5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5
    YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5
    YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5
    YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5
    YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5
    YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5YqY5
    =FakeKey
    -----END PGP PUBLIC KEY BLOCK-----

    Contact via secure session only. No clearnet comms.

    - Vendor_ShadowX
    """

    print("=" * 60)
    print("IntelligenceExtractor Standalone Test")
    print("=" * 60)

    extractor = IntelligenceExtractor()
    result = extractor.parse_document(mock_forum_post)

    print("\nExtracted Indicators:")
    print(json.dumps(result, indent=4))

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)