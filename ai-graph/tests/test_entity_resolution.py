"""Unit tests for entity resolution and cross-marketplace persona linkage."""
from typing import List
import pytest

from ai.entity_resolution import EntityResolver, LinkageDecision
from ai.ollama_client import OllamaStylometryService
from nlp.identifier_extractor import IdentifierExtractor
from nlp.stylometry import StylometryExtractor
from schemas.extracted_features import (
    CryptoWallet,
    ExtractedIdentifiers,
    StylometricFeatures,
    ThreatActorProfile,
)
from schemas.raw_post import RawForumPost


@pytest.fixture
def resolver() -> EntityResolver:
    """Fixture providing EntityResolver configured with deterministic mock service."""
    mock_ollama = OllamaStylometryService(mock=True)
    return EntityResolver(threshold=0.80, ollama_service=mock_ollama)


def _build_profile_from_posts(
    handle: str,
    platform: str,
    posts: List[RawForumPost],
    stylometry: StylometryExtractor,
    identifiers: IdentifierExtractor,
    ollama: OllamaStylometryService,
) -> ThreatActorProfile:
    """Helper to aggregate posts into a composite ThreatActorProfile."""
    combined_text = " ".join(p.raw_content for p in posts)

    features = stylometry.extract_features(combined_text)
    features.embedding = ollama.generate_embedding(combined_text)

    extracted_ids = identifiers.extract_all(combined_text)

    return ThreatActorProfile(
        handle=handle,
        platform=platform,
        features=features,
        identifiers=extracted_ids,
        attribution_id=f"actor-{handle.lower()}",
    )


def test_persona_a_and_c_resolve_to_same_cluster(
    resolver: EntityResolver,
    sample_posts: List[RawForumPost],
):
    """Core acceptance test: Persona A (ShadowBroker) and Persona C (GhostMigrant) resolve to the same actor with confidence >= 0.80."""
    stylometry = StylometryExtractor()
    identifiers = IdentifierExtractor()
    ollama = resolver.ollama_service

    posts_a = [p for p in sample_posts if p.author_handle == "ShadowBroker"]
    posts_c = [p for p in sample_posts if p.author_handle == "GhostMigrant"]

    profile_a = _build_profile_from_posts("ShadowBroker", "DreadClone", posts_a, stylometry, identifiers, ollama)
    profile_c = _build_profile_from_posts("GhostMigrant", "AlphaVendor", posts_c, stylometry, identifiers, ollama)

    # Resolve Candidate C against Existing Profile A
    decision = resolver.compare_profiles(profile_c, profile_a)

    assert decision.matched is True
    assert decision.confidence_score >= 0.80
    assert len(decision.link_reasons) > 0
    # Audit trail verifies explainability
    assert any("cryptocurrency wallet" in r.lower() or "pgp" in r.lower() or "stylometric" in r.lower() for r in decision.link_reasons)


def test_persona_b_and_d_do_not_resolve_to_persona_a(
    resolver: EntityResolver,
    sample_posts: List[RawForumPost],
):
    """Verify negative controls: CryptoRebel and ScriptKiddie do not link to ShadowBroker."""
    stylometry = StylometryExtractor()
    identifiers = IdentifierExtractor()
    ollama = resolver.ollama_service

    posts_a = [p for p in sample_posts if p.author_handle == "ShadowBroker"]
    posts_b = [p for p in sample_posts if p.author_handle == "CryptoRebel"]
    posts_d = [p for p in sample_posts if p.author_handle == "ScriptKiddie"]

    profile_a = _build_profile_from_posts("ShadowBroker", "DreadClone", posts_a, stylometry, identifiers, ollama)
    profile_b = _build_profile_from_posts("CryptoRebel", "BreachNode", posts_b, stylometry, identifiers, ollama)
    profile_d = _build_profile_from_posts("ScriptKiddie", "DreadClone", posts_d, stylometry, identifiers, ollama)

    decision_b = resolver.compare_profiles(profile_b, profile_a)
    assert decision_b.matched is False
    assert decision_b.confidence_score < 0.60

    decision_d = resolver.compare_profiles(profile_d, profile_a)
    assert decision_d.matched is False
    assert decision_d.confidence_score < 0.50


def test_hard_identifier_alone_triggers_high_confidence(resolver: EntityResolver):
    """Verify exact shared wallet or PGP key triggers confidence >= 0.95 even with neutral stylometry."""
    profile_x = ThreatActorProfile(
        handle="VendorX",
        platform="DarkForum1",
        features=StylometricFeatures(average_sentence_length=15.0),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="BTC", address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")],
        ),
    )

    profile_y = ThreatActorProfile(
        handle="VendorY",
        platform="DarkForum2",
        features=StylometricFeatures(average_sentence_length=25.0),  # different syntax
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="BTC", address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")],
        ),
    )

    decision = resolver.compare_profiles(profile_x, profile_y)
    assert decision.matched is True
    assert decision.confidence_score >= 0.95
    assert any("wallet" in r.lower() for r in decision.link_reasons)


def test_pure_stylometric_similarity_linking(resolver: EntityResolver):
    """Verify strong behavioral stylometry links actors even without shared hard identifiers."""
    # Shared clipped ellipses writing style, no shared wallets or PGP
    features_a = StylometricFeatures(
        average_sentence_length=6.0,
        average_word_length=4.5,
        uppercase_ratio=0.35,
        type_token_ratio=0.60,
        punctuation_frequency={"...": 5, "!": 2},
        embedding=[0.8, 0.6, 0.0],
    )
    features_b = StylometricFeatures(
        average_sentence_length=6.5,
        average_word_length=4.6,
        uppercase_ratio=0.32,
        type_token_ratio=0.62,
        punctuation_frequency={"...": 4, "!": 1},
        embedding=[0.8, 0.6, 0.0],  # Cosine similarity 1.0
    )

    profile_1 = ThreatActorProfile(
        handle="AnonSeller1",
        platform="MarketA",
        features=features_a,
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="BTC", address="bc1qwallet11111111111111111111111111111111111")],
        ),
    )
    profile_2 = ThreatActorProfile(
        handle="AnonSeller2",
        platform="MarketB",
        features=features_b,
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="BTC", address="bc1qwallet22222222222222222222222222222222222")],
        ),
    )

    decision = resolver.compare_profiles(profile_1, profile_2)
    assert decision.matched is True
    assert decision.confidence_score >= 0.80
    assert any("stylometric" in r.lower() for r in decision.link_reasons)


def test_cluster_profiles_batch(resolver: EntityResolver, sample_posts: List[RawForumPost]):
    """Verify multi-persona clustering groups Persona A and C while isolating B and D."""
    stylometry = StylometryExtractor()
    identifiers = IdentifierExtractor()
    ollama = resolver.ollama_service

    profiles = []
    for h, p in [
        ("ShadowBroker", "DreadClone"),
        ("CryptoRebel", "BreachNode"),
        ("GhostMigrant", "AlphaVendor"),
        ("ScriptKiddie", "DreadClone"),
    ]:
        posts = [post for post in sample_posts if post.author_handle == h]
        prof = _build_profile_from_posts(h, p, posts, stylometry, identifiers, ollama)
        profiles.append(prof)

    clusters = resolver.cluster_profiles(profiles)

    # ShadowBroker and GhostMigrant must be in the same cluster
    cluster_sb = next(cid for cid, plist in clusters.items() if any(p.handle == "ShadowBroker" for p in plist))
    cluster_gm = next(cid for cid, plist in clusters.items() if any(p.handle == "GhostMigrant" for p in plist))
    assert cluster_sb == cluster_gm

    # CryptoRebel and ScriptKiddie must be in separate clusters
    cluster_cr = next(cid for cid, plist in clusters.items() if any(p.handle == "CryptoRebel" for p in plist))
    cluster_sk = next(cid for cid, plist in clusters.items() if any(p.handle == "ScriptKiddie" for p in plist))
    assert cluster_cr != cluster_sb
    assert cluster_sk != cluster_sb
    assert cluster_cr != cluster_sk
