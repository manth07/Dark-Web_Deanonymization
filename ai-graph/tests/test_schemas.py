"""Unit tests for Pydantic data schemas and configuration settings."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from config import Settings
from schemas.raw_post import RawForumPost
from schemas.extracted_features import (
    CryptoWallet,
    ExtractedIdentifiers,
    StylometricFeatures,
    ThreatActorProfile,
)


def test_settings_defaults():
    """Verify application settings load proper defaults and validate boundaries."""
    settings = Settings()
    assert "7687" in settings.NEO4J_URI
    assert settings.NEO4J_USER == "neo4j"
    assert "11434" in settings.OLLAMA_BASE_URL
    assert settings.SIMILARITY_THRESHOLD == 0.82

    # Verify default without .env override
    clean_settings = Settings(_env_file=None)
    assert clean_settings.NEO4J_URI == "bolt://localhost:7687"
    assert clean_settings.OLLAMA_BASE_URL == "http://localhost:11434"

    # Threshold must be within 0.0 and 1.0
    with pytest.raises(ValidationError):
        Settings(SIMILARITY_THRESHOLD=1.5)

    with pytest.raises(ValidationError):
        Settings(SIMILARITY_THRESHOLD=-0.1)


def test_raw_post_serialization_and_deserialization():
    """Verify RawForumPost parses standard fields and serializes to JSON."""
    now = datetime.now(timezone.utc)
    post_data = {
        "post_id": "post-101",
        "forum_name": "DreadClone",
        "author_handle": "ShadowBroker",
        "raw_content": "Selling zero-day exploit packages... Contact via PGP.",
        "timestamp": now.isoformat(),
        "thread_title": "0day Database Dump",
        "source_url": "http://dreadclone.onion/t/101",
    }

    post = RawForumPost(**post_data)
    assert post.post_id == "post-101"
    assert post.forum_name == "DreadClone"
    assert post.author_handle == "ShadowBroker"
    assert "Selling zero-day" in post.raw_content
    assert post.thread_title == "0day Database Dump"

    # Verify JSON round-trip
    dumped_json = post.model_dump_json()
    reconstructed = RawForumPost.model_validate_json(dumped_json)
    assert reconstructed.post_id == post.post_id
    assert reconstructed.forum_name == post.forum_name


def test_raw_post_aliases_from_scraping_spec():
    """Verify RawForumPost correctly aliases scraper contract fields."""
    scraper_record = {
        "record_id": "uuid-8899",
        "marketplace": "AlphaVendor",
        "actor_handle": "GhostMigrant",
        "raw_text": "Need escrow service for high volume transaction.",
        "timestamp": "2026-09-22T10:00:00Z",
    }

    post = RawForumPost.model_validate(scraper_record)
    assert post.post_id == "uuid-8899"
    assert post.forum_name == "AlphaVendor"
    assert post.author_handle == "GhostMigrant"
    assert post.raw_content == "Need escrow service for high volume transaction."


def test_stylometric_features_constraints():
    """Verify bounds and defaults on StylometricFeatures."""
    features = StylometricFeatures(
        average_sentence_length=14.5,
        average_word_length=4.8,
        type_token_ratio=0.65,
        hapax_legomena_ratio=0.45,
        punctuation_frequency={"!": 3, "...": 2},
        pos_tag_distribution={"NOUN": 0.35, "VERB": 0.25},
        function_word_frequency={"the": 0.05, "and": 0.03},
        paragraph_count=2,
        uppercase_ratio=0.08,
        character_count=450,
        embedding=[0.12, -0.45, 0.88],
    )

    assert features.average_sentence_length == 14.5
    assert features.punctuation_frequency["..."] == 2
    assert len(features.embedding) == 3

    # Invalid constraints
    with pytest.raises(ValidationError):
        StylometricFeatures(type_token_ratio=1.5)

    with pytest.raises(ValidationError):
        StylometricFeatures(uppercase_ratio=-0.1)


def test_extracted_identifiers_and_wallets():
    """Verify ExtractedIdentifiers and CryptoWallet data integrity."""
    wallet_btc = CryptoWallet(currency="BTC", address="bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
    wallet_xmr = CryptoWallet(currency="XMR", address="44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otKEfZagUopA9996oReoStZ6CHngAoRMa25VrWAFGLvmjh323")

    identifiers = ExtractedIdentifiers(
        crypto_wallets=[wallet_btc, wallet_xmr],
        pgp_keys=["4A5B6C7D8E9F0A1B2C3D4E5F6A7B8C9D0E1F2A3B"],
        ip_addresses=["198.51.100.42"],
    )

    assert len(identifiers.crypto_wallets) == 2
    assert identifiers.crypto_wallets[0].currency == "BTC"
    assert identifiers.pgp_keys[0].startswith("4A5B")
    assert identifiers.ip_addresses[0] == "198.51.100.42"


def test_threat_actor_profile_aggregation():
    """Verify ThreatActorProfile combines features, identifiers, and attribution ID."""
    profile = ThreatActorProfile(
        handle="CryptoRebel",
        platform="BreachNode",
        features=StylometricFeatures(
            average_sentence_length=22.0,
            average_word_length=5.6,
            type_token_ratio=0.72,
        ),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="ETH", address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F")],
        ),
        attribution_id="actor-uuid-007",
    )

    data = profile.model_dump()
    assert data["handle"] == "CryptoRebel"
    assert data["platform"] == "BreachNode"
    assert data["features"]["average_sentence_length"] == 22.0
    assert data["identifiers"]["crypto_wallets"][0]["currency"] == "ETH"
    assert data["attribution_id"] == "actor-uuid-007"
