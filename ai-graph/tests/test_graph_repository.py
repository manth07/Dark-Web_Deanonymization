"""Integration and unit tests for Neo4j Threat Graph Repository."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from graph.driver import Neo4jDriver
from graph.repository import (
    ThreatGraphRepository,
    UPSERT_PERSONA_POST_QUERY,
    LINK_CRYPTO_WALLET_QUERY,
    LINK_PGP_KEY_QUERY,
    LINK_IP_ADDRESS_QUERY,
    CREATE_ATTRIBUTION_LINK_QUERY,
)
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
def repo(tmp_path):
    """Fresh repository instance with temp-isolated in-memory store."""
    temp_store = str(tmp_path / "test_graph_repo.json")
    repository = ThreatGraphRepository(store_path=temp_store)
    repository.clear()
    return repository


def test_upsert_persona_and_relationships(repo):
    """Verify upsert_persona creates persona, post, and identifier edges in the graph topology."""
    profile = ThreatActorProfile(
        handle="ShadowBroker",
        platform="DreadClone",
        features=StylometricFeatures(
            average_sentence_length=15.5,
            average_word_length=5.1,
            type_token_ratio=0.72,
            hapax_legomena_ratio=0.55,
            paragraph_count=3,
            uppercase_ratio=0.08,
            character_count=450,
        ),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[
                CryptoWallet(currency="XMR", address="44AFFq5kSiGBoZ4NMDwYtN18obcGWvUZn17bZcG8dW27MBR5Vyc"),
                CryptoWallet(currency="BTC", address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"),
            ],
            pgp_keys=["9B8D7C6E5F4A3B2C1D0E9F8A7B6C5D4E3F2A1B0C"],
            ip_addresses=["198.51.100.25"],
        ),
    )

    post = RawForumPost(
        post_id="post_test_001",
        forum_name="DreadClone",
        author_handle="ShadowBroker",
        raw_content="Offering zero-day leaks. Payment strictly in XMR.",
        timestamp=datetime.now(timezone.utc),
    )

    repo.upsert_persona(profile, post)

    # Verify candidate profiles retrieval reflects the upserted data
    candidates = repo.get_candidate_profiles()
    assert len(candidates) == 1
    stored = candidates[0]
    assert stored.handle == "ShadowBroker"
    assert stored.platform == "DreadClone"
    assert stored.features.average_sentence_length == 15.5
    assert len(stored.identifiers.crypto_wallets) == 2
    assert len(stored.identifiers.pgp_keys) == 1
    assert stored.identifiers.pgp_keys[0] == "9B8D7C6E5F4A3B2C1D0E9F8A7B6C5D4E3F2A1B0C"
    assert stored.identifiers.ip_addresses == ["198.51.100.25"]


def test_upsert_persona_idempotency(repo):
    """Verify repeated upsert_persona calls do not duplicate nodes or edges."""
    profile = ThreatActorProfile(
        handle="ShadowBroker",
        platform="DreadClone",
        features=StylometricFeatures(average_sentence_length=15.0),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="XMR", address="44AFFq5kSiGBoZ4NMDwYtN18obcGWvUZn17bZcG8dW27MBR5Vyc")],
        ),
    )
    post = RawForumPost(
        post_id="post_idempotent_001",
        forum_name="DreadClone",
        author_handle="ShadowBroker",
        raw_content="Idempotency test.",
    )

    # First call
    repo.upsert_persona(profile, post)
    # Second call with identical payload
    repo.upsert_persona(profile, post)

    candidates = repo.get_candidate_profiles()
    assert len(candidates) == 1
    assert len(repo._in_memory_store["personas"]) == 1
    assert len(repo._in_memory_store["posts"]) == 1
    assert len(repo._in_memory_store["authored"]) == 1
    assert len(repo._in_memory_store["utilizes_wallet"]) == 1


def test_create_attribution_link_and_query_actor_network(repo):
    """Verify creating attribution links between personas and querying actor network topology."""
    # 1. Upsert Persona A
    profile_a = ThreatActorProfile(
        handle="ShadowBroker",
        platform="DreadClone",
        features=StylometricFeatures(average_sentence_length=12.0),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="XMR", address="44AFFq5kSiGBoZ4NMDwYtN18obcGWvUZn17bZcG8dW27MBR5Vyc")],
            ip_addresses=["198.51.100.25"],
        ),
    )
    post_a = RawForumPost(
        post_id="post_a_001",
        forum_name="DreadClone",
        author_handle="ShadowBroker",
        raw_content="Post on Dread.",
    )
    repo.upsert_persona(profile_a, post_a)

    # 2. Upsert Persona C
    profile_c = ThreatActorProfile(
        handle="GhostMigrant",
        platform="AlphaVendor",
        features=StylometricFeatures(average_sentence_length=12.2),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="XMR", address="44AFFq5kSiGBoZ4NMDwYtN18obcGWvUZn17bZcG8dW27MBR5Vyc")],
            pgp_keys=["8A7B6C5D4E3F2A1B0C9D8E7F6A5B4C3D2E1F0A9B"],
        ),
    )
    post_c = RawForumPost(
        post_id="post_c_001",
        forum_name="AlphaVendor",
        author_handle="GhostMigrant",
        raw_content="Migrated to AlphaVendor.",
    )
    repo.upsert_persona(profile_c, post_c)

    # 3. Create Attribution Link
    actor_id = "actor_cluster_test_001"
    repo.create_attribution_link(
        actor_id=actor_id,
        persona_a_key={"handle": "ShadowBroker", "platform": "DreadClone"},
        persona_b_key={"handle": "GhostMigrant", "platform": "AlphaVendor"},
        confidence=0.96,
        reasons=["Exact Monero wallet match", "High stylometric similarity (0.88)"],
    )

    # 4. Query Actor Network
    network = repo.query_actor_network(actor_id)

    assert network["actor_id"] == actor_id
    assert network["attribution_confidence"] >= 0.90
    assert len(network["handles"]) == 2
    handles = {h["handle"] for h in network["handles"]}
    assert handles == {"ShadowBroker", "GhostMigrant"}

    assert set(network["marketplaces"]) == {"AlphaVendor", "DreadClone"}
    assert network["total_posts"] == 2
    assert network["total_wallets"] == 1
    assert network["crypto_wallets"][0]["currency"] == "XMR"
    assert "198.51.100.25" in network["ip_addresses"]
    assert "8A7B6C5D4E3F2A1B0C9D8E7F6A5B4C3D2E1F0A9B" in network["pgp_keys"]

    # Linkages
    assert len(network["linkages"]) == 1
    link = network["linkages"][0]
    assert link["source_handle"] == "ShadowBroker"
    assert link["target_handle"] == "GhostMigrant"
    assert link["confidence"] == 0.96
    assert "Exact Monero wallet match" in link["reasons"]


def test_query_actor_network_nonexistent(repo):
    """Verify querying non-existent actor returns safe empty structure without crashing."""
    result = repo.query_actor_network("non_existent_actor_999")
    assert result["actor_id"] == "non_existent_actor_999"
    assert result["attribution_confidence"] == 0.0
    assert result["handles"] == []
    assert result["marketplaces"] == []
    assert result["crypto_wallets"] == []
    assert result["total_posts"] == 0


def test_cypher_generation_with_mock_driver():
    """Verify exact parameterized Cypher write calls when driver is active."""
    mock_driver = MagicMock(spec=Neo4jDriver)
    mock_driver.verify_connectivity.return_value = True

    repo = ThreatGraphRepository(driver=mock_driver)

    profile = ThreatActorProfile(
        handle="TestActor",
        platform="TestForum",
        features=StylometricFeatures(average_sentence_length=14.0),
        identifiers=ExtractedIdentifiers(
            crypto_wallets=[CryptoWallet(currency="BTC", address="1TestAddressBTC")],
            pgp_keys=["ABCD1234EF567890"],
            ip_addresses=["198.51.100.1"],
        ),
    )
    post = RawForumPost(
        post_id="post_mock_001",
        forum_name="TestForum",
        author_handle="TestActor",
        raw_content="Cypher test content",
    )

    # 1. Test upsert_persona Cypher queries
    repo.upsert_persona(profile, post)

    # Check calls to execute_write: 1 for persona/post + 1 wallet + 1 pgp + 1 ip = 4 calls
    assert mock_driver.execute_write.call_count == 4

    # Check that queries contain required Cypher statements
    call_args_list = mock_driver.execute_write.call_args_list
    queries_run = [call[0][0] for call in call_args_list]

    assert any("MERGE (p:Persona {handle: $handle, platform: $platform})" in q for q in queries_run)
    assert any("MERGE (w:CryptoWallet {address: $address})" in q for q in queries_run)
    assert any("MERGE (k:PGPKey {fingerprint: $fingerprint})" in q for q in queries_run)
    assert any("MERGE (i:IPAddress {ip: $ip})" in q for q in queries_run)

    # 2. Test create_attribution_link Cypher query
    mock_driver.reset_mock()
    repo.create_attribution_link(
        actor_id="actor_mock_cluster",
        persona_a_key={"handle": "ActorA", "platform": "ForumA"},
        persona_b_key={"handle": "ActorB", "platform": "ForumB"},
        confidence=0.88,
        reasons=["High stylometric similarity"],
    )

    assert mock_driver.execute_write.call_count == 1
    link_query, link_params = mock_driver.execute_write.call_args[0]
    assert "MERGE (t:ThreatActor {actor_id: $actor_id})" in link_query
    assert "MERGE (p1)-[r:LINKED_TO {method: 'stylometry_v1'}]->(p2)" in link_query
    assert link_params["actor_id"] == "actor_mock_cluster"
    assert link_params["handle_a"] == "ActorA"
    assert link_params["handle_b"] == "ActorB"
    assert link_params["confidence"] == 0.88


def test_synthetic_posts_ingestion_integration(repo, sample_posts):
    """End-to-end integration test pushing synthetic persona posts from corpus into repository."""
    stylometry_extractor = StylometryExtractor()
    identifier_extractor = IdentifierExtractor()

    # Filter posts for ShadowBroker (Persona A) and GhostMigrant (Persona C)
    actor_a_posts = [p for p in sample_posts if p.author_handle == "ShadowBroker"]
    actor_c_posts = [p for p in sample_posts if p.author_handle == "GhostMigrant"]

    assert len(actor_a_posts) > 0
    assert len(actor_c_posts) > 0

    # Ingest Persona A posts
    for post in actor_a_posts:
        features = stylometry_extractor.extract_features(post.raw_content)
        identifiers = identifier_extractor.extract_all(post.raw_content)
        profile = ThreatActorProfile(
            handle=post.author_handle,
            platform=post.forum_name,
            features=features,
            identifiers=identifiers,
        )
        repo.upsert_persona(profile, post)

    # Ingest Persona C posts
    for post in actor_c_posts:
        features = stylometry_extractor.extract_features(post.raw_content)
        identifiers = identifier_extractor.extract_all(post.raw_content)
        profile = ThreatActorProfile(
            handle=post.author_handle,
            platform=post.forum_name,
            features=features,
            identifiers=identifiers,
        )
        repo.upsert_persona(profile, post)

    # Link Persona A and Persona C into a single threat actor
    cluster_id = "actor_cluster_shadow_ghost"
    repo.create_attribution_link(
        actor_id=cluster_id,
        persona_a_key={"handle": "ShadowBroker", "platform": "DreadClone"},
        persona_b_key={"handle": "GhostMigrant", "platform": "AlphaVendor"},
        confidence=0.92,
        reasons=["Shared Monero wallet address", "Clipped sentence syntax overlap"],
    )

    # Verify query_actor_network
    network = repo.query_actor_network(cluster_id)
    assert network["actor_id"] == cluster_id
    assert len(network["handles"]) == 2
    assert network["total_posts"] == len(actor_a_posts) + len(actor_c_posts)
    assert network["total_wallets"] >= 1
    assert "AlphaVendor" in network["marketplaces"]
    assert "DreadClone" in network["marketplaces"]
