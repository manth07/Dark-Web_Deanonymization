"""End-to-End integration test suite for Dark Web Threat Actor Deanonymization Engine.

Conforms to Loop 6: Prompt 6.2 in Brain/prompts.md:
1. Verifies database connectivity or graceful offline fallback.
2. Ingests full synthetic dataset (sample_posts.json) end-to-end.
3. Confirms Persona C (GhostMigrant) is successfully resolved and linked to Persona A (ShadowBroker).
4. Verifies isolation of unrelated personas (CryptoRebel and ScriptKiddie).
5. Exports and validates NTRO intelligence deliverable JSON and analyst CSV formats.
"""
import csv
import json
from pathlib import Path
import pytest

from export.reporter import IntelligenceReporter
from graph.repository import ThreatGraphRepository
from pipeline import StylometryPipeline
from schemas.raw_post import RawForumPost


@pytest.fixture
def e2e_env(tmp_path):
    """Isolated end-to-end test environment with temporary graph store and export paths."""
    graph_store_path = str(tmp_path / "e2e_graph_store.json")
    export_dir = tmp_path / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    repo = ThreatGraphRepository(store_path=graph_store_path)
    repo.clear()

    pipeline = StylometryPipeline(repository=repo)
    reporter = IntelligenceReporter(repository=repo)

    return {
        "repo": repo,
        "pipeline": pipeline,
        "reporter": reporter,
        "export_dir": export_dir,
    }


def test_e2e_pipeline_full_run_and_attribution(e2e_env, sample_posts):
    """End-to-end execution of full pipeline against synthetic forum post corpus."""
    pipeline = e2e_env["pipeline"]
    repo = e2e_env["repo"]
    reporter = e2e_env["reporter"]
    export_dir = e2e_env["export_dir"]

    # 1. Ingest all 24 posts from sample_posts.json
    assert len(sample_posts) == 24
    processed = pipeline.process_batch(sample_posts)
    assert len(processed) == 24

    # 2. Query candidate profiles from repository
    candidate_profiles = repo.get_candidate_profiles()
    assert len(candidate_profiles) == 4

    handles_map = {p.handle: p for p in candidate_profiles}
    assert "ShadowBroker" in handles_map
    assert "GhostMigrant" in handles_map
    assert "CryptoRebel" in handles_map
    assert "ScriptKiddie" in handles_map

    # 3. Confirm Persona C (GhostMigrant) is successfully linked to Persona A (ShadowBroker)
    sb_profile = handles_map["ShadowBroker"]
    gm_profile = handles_map["GhostMigrant"]
    cr_profile = handles_map["CryptoRebel"]
    sk_profile = handles_map["ScriptKiddie"]

    assert sb_profile.attribution_id is not None
    assert gm_profile.attribution_id is not None
    # Must resolve to the exact same canonical ThreatActor cluster
    assert sb_profile.attribution_id == gm_profile.attribution_id
    linked_actor_id = sb_profile.attribution_id

    # 4. Verify negative controls (unrelated personas are not falsely linked)
    assert cr_profile.attribution_id != linked_actor_id
    assert sk_profile.attribution_id != linked_actor_id
    assert cr_profile.attribution_id != sk_profile.attribution_id

    # 5. Query actor network topology for the resolved cluster
    network = repo.query_actor_network(linked_actor_id)
    assert network["actor_id"] == linked_actor_id
    assert network["attribution_confidence"] >= 0.80

    handles = {h["handle"] for h in network["handles"]}
    assert handles == {"ShadowBroker", "GhostMigrant"}

    marketplaces = set(network["marketplaces"])
    assert marketplaces == {"AlphaVendor", "DreadClone"}

    # Total posts from both handles (6 posts each = 12 posts)
    assert network["total_posts"] == 12

    # Technical Indicators: Wallets and PGP
    assert network["total_wallets"] >= 1
    wallet_addresses = [w["address"] for w in network["crypto_wallets"]]
    assert any("bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s" in addr for addr in wallet_addresses)

    assert len(network["pgp_keys"]) >= 1
    assert len(network["linkages"]) >= 1


def test_e2e_export_ntro_json_deliverable(e2e_env, sample_posts):
    """Validate that exported JSON deliverable strictly conforms to NTRO intelligence deliverable specifications."""
    pipeline = e2e_env["pipeline"]
    reporter = e2e_env["reporter"]
    export_dir = e2e_env["export_dir"]

    # Ingest corpus
    pipeline.process_batch(sample_posts)

    # Find Persona A/C cluster
    candidates = e2e_env["repo"].get_candidate_profiles()
    sb = next(p for p in candidates if p.handle == "ShadowBroker")
    actor_id = sb.attribution_id
    assert actor_id is not None

    # Export JSON
    json_path = export_dir / f"{actor_id}.json"
    deliverable = reporter.export_json(actor_id, str(json_path))

    # Validate file was written to disk
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        file_data = json.load(f)

    # Validate NTRO schema structure and required indicators
    assert file_data["root_actor_id"] == actor_id
    assert file_data["attribution_confidence"] >= 0.80
    assert "GhostMigrant" in file_data["alias_handles"]
    assert "ShadowBroker" in file_data["alias_handles"]
    assert set(file_data["platforms"]) == {"AlphaVendor", "DreadClone"}
    assert len(file_data["crypto_wallets"]) >= 1
    assert len(file_data["pgp_fingerprints"]) >= 1
    assert len(file_data["timestamp_timeline"]) == 12

    # Verify timeline sorting is chronological
    timestamps = [p["timestamp"] for p in file_data["timestamp_timeline"]]
    assert timestamps == sorted(timestamps)

    # Metadata audit trail
    assert "classification" in file_data["metadata"]
    assert "LAW ENFORCEMENT SENSITIVE" in file_data["metadata"]["classification"]

    # Executive Briefing Narrative
    assert "summary_briefing" in file_data
    assert "NTRO THREAT INTELLIGENCE BRIEFING" in file_data["summary_briefing"]
    assert "GhostMigrant" in file_data["summary_briefing"]
    assert "ShadowBroker" in file_data["summary_briefing"]


def test_e2e_export_analyst_csv_deliverable(e2e_env, sample_posts):
    """Validate that exported CSV analyst deliverable contains properly flattened tabular mappings."""
    pipeline = e2e_env["pipeline"]
    reporter = e2e_env["reporter"]
    export_dir = e2e_env["export_dir"]

    # Ingest corpus
    pipeline.process_batch(sample_posts)

    candidates = e2e_env["repo"].get_candidate_profiles()
    sb = next(p for p in candidates if p.handle == "ShadowBroker")
    actor_id = sb.attribution_id

    # Export CSV
    csv_path = export_dir / f"{actor_id}.csv"
    reporter.export_csv(actor_id, str(csv_path))

    assert csv_path.exists()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) > 0
    # Validate column fields
    expected_fields = [
        "actor_id",
        "handle",
        "platform",
        "identifier_type",
        "identifier_value",
        "attribution_confidence",
    ]
    for field in expected_fields:
        assert field in reader[0]

    # Verify rows reflect persona-to-identifier mappings
    handles = {row["handle"] for row in reader}
    assert "ShadowBroker" in handles
    assert "GhostMigrant" in handles

    identifier_types = {row["identifier_type"] for row in reader}
    assert any("crypto_wallet" in it for it in identifier_types)
    assert any("pgp_key" in it for it in identifier_types)


def test_e2e_summary_briefing_narrative(e2e_env, sample_posts):
    """Validate textual intelligence briefing format against NTRO reporting guidelines."""
    pipeline = e2e_env["pipeline"]
    reporter = e2e_env["reporter"]

    pipeline.process_batch(sample_posts)

    candidates = e2e_env["repo"].get_candidate_profiles()
    sb = next(p for p in candidates if p.handle == "ShadowBroker")
    actor_id = sb.attribution_id

    briefing = reporter.generate_summary_report(actor_id)

    assert "[NTRO THREAT INTELLIGENCE BRIEFING]" in briefing
    assert f"Threat Actor [{actor_id}]" in briefing
    assert "operates across 2 marketplace(s)" in briefing
    assert "GhostMigrant" in briefing
    assert "ShadowBroker" in briefing
    assert "Attribution Confidence:" in briefing
    assert "Harvested Cryptographic & Infrastructure Indicators:" in briefing
    assert "Wallets:" in briefing
    assert "Total Observed Forum Posts: 12" in briefing
