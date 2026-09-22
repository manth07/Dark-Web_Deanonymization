"""Unit tests for cryptocurrency wallet, PGP key, and IP address extraction."""
from typing import List
import pytest

from nlp.identifier_extractor import IdentifierExtractor
from schemas.raw_post import RawForumPost


@pytest.fixture(scope="module")
def extractor() -> IdentifierExtractor:
    """Fixture providing initialized IdentifierExtractor."""
    return IdentifierExtractor()


def test_bitcoin_extraction(extractor: IdentifierExtractor):
    """Verify extraction of Bitcoin P2PKH, P2SH, and Bech32 addresses."""
    text = (
        "Send payments to legacy P2PKH 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa or "
        "multisig P2SH 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy or "
        "native segwit bech32 bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq for discount."
    )

    wallets = extractor.extract_crypto_wallets(text)
    btc_wallets = [w for w in wallets if w.currency == "BTC"]
    addresses = {w.address for w in btc_wallets}

    assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in addresses
    assert "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy" in addresses
    assert "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq" in addresses


def test_monero_extraction(extractor: IdentifierExtractor):
    """Verify extraction of Monero standard 95-char and integrated 106-char addresses."""
    standard_xmr = "44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otKEfZagUopA9996oReoStZ6CHngAoRMa25VrWAFGLvmjh2QW51Uv"
    # Integrated address: starts with 8, 106 characters
    integrated_xmr = "888tNkZrPN6JsEgekjMnABU4TBzc2Dt29EPAvkFxbANsAnJYPbb3iQ1YBRk1UXcdRsiKc9dhwMVgN5S9cQUiyoogDavup3H2KcmVvDKeCa"

    text = f"Monero primary: {standard_xmr} and secondary integrated: {integrated_xmr}."
    wallets = extractor.extract_crypto_wallets(text)
    xmr_wallets = [w for w in wallets if w.currency == "XMR"]
    addresses = {w.address for w in xmr_wallets}

    assert standard_xmr in addresses
    assert integrated_xmr in addresses


def test_ethereum_extraction(extractor: IdentifierExtractor):
    """Verify extraction of Ethereum addresses."""
    eth_addr = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    text = f"Only accepting Ethereum payments to {eth_addr} bro fast deal!"

    wallets = extractor.extract_crypto_wallets(text)
    eth_wallets = [w for w in wallets if w.currency == "ETH"]

    assert len(eth_wallets) == 1
    assert eth_wallets[0].address == eth_addr


def test_pgp_key_and_fingerprint_extraction(extractor: IdentifierExtractor):
    """Verify extraction of PGP ASCII-armored key blocks and 40-character fingerprints."""
    key_block = (
        "-----BEGIN PGP PUBLIC KEY BLOCK-----\n"
        "Version: BCPG C# v1.6.1.0\n\n"
        "mQENBF2v6wEBCADL+SAMPLE+PGP+BLOCK+DATA==\n"
        "-----END PGP PUBLIC KEY BLOCK-----"
    )
    fp_contiguous = "4A5B6C7D8E9F0A1B2C3D4E5F6A7B8C9D0E1F2A3B"
    fp_spaced = "4A5B 6C7D 8E9F 0A1B 2C3D 4E5F 6A7B 8C9D 0E1F 2A3B"

    text = f"Here is my public key:\n{key_block}\nFingerprint: {fp_contiguous}\nBackup: {fp_spaced}"

    pgp_items = extractor.extract_pgp_keys(text)

    # Check block is extracted
    assert any("BEGIN PGP PUBLIC KEY BLOCK" in item for item in pgp_items)
    # Check fingerprint is extracted
    assert fp_contiguous in pgp_items


def test_ip_address_filtering(extractor: IdentifierExtractor):
    """Verify extraction of public IPv4 addresses while filtering private and loopback ranges."""
    text = (
        "Server leaking info at 198.51.100.23 and test host 203.0.113.89. "
        "Do not connect to localhost 127.0.0.1 or router 192.168.1.1 or internal 10.0.0.1!"
    )

    public_ips = extractor.extract_ip_addresses(text, include_private=False)
    assert "198.51.100.23" in public_ips
    assert "203.0.113.89" in public_ips
    assert "127.0.0.1" not in public_ips
    assert "192.168.1.1" not in public_ips
    assert "10.0.0.1" not in public_ips

    # When private IPs are allowed
    all_ips = extractor.extract_ip_addresses(text, include_private=True)
    assert "127.0.0.1" in all_ips
    assert "192.168.1.1" in all_ips
    assert "10.0.0.1" in all_ips


def test_extract_all_on_synthetic_posts(extractor: IdentifierExtractor, sample_posts: List[RawForumPost]):
    """Verify end-to-end indicator harvesting across the generated dark web corpus."""
    actor_indicators = {}
    for post in sample_posts:
        identifiers = extractor.extract_all(post.raw_content)
        handle = post.author_handle
        if handle not in actor_indicators:
            actor_indicators[handle] = {
                "wallets": [],
                "pgp": [],
                "ips": [],
            }
        actor_indicators[handle]["wallets"].extend(identifiers.crypto_wallets)
        actor_indicators[handle]["pgp"].extend(identifiers.pgp_keys)
        actor_indicators[handle]["ips"].extend(identifiers.ip_addresses)

    # ShadowBroker: BTC wallet & PGP
    sb_wallets = actor_indicators["ShadowBroker"]["wallets"]
    assert any(w.currency == "BTC" for w in sb_wallets)
    assert len(actor_indicators["ShadowBroker"]["pgp"]) > 0

    # CryptoRebel: Monero (XMR)
    cr_wallets = actor_indicators["CryptoRebel"]["wallets"]
    assert any(w.currency == "XMR" for w in cr_wallets)

    # GhostMigrant: BTC wallet & PGP
    gm_wallets = actor_indicators["GhostMigrant"]["wallets"]
    assert any(w.currency == "BTC" for w in gm_wallets)
    assert len(actor_indicators["GhostMigrant"]["pgp"]) > 0

    # ScriptKiddie: ETH wallet & clearnet public IPs
    sk_wallets = actor_indicators["ScriptKiddie"]["wallets"]
    assert any(w.currency == "ETH" for w in sk_wallets)
    assert len(actor_indicators["ScriptKiddie"]["ips"]) > 0
