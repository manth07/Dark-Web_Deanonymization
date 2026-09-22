"""Unit and integration tests for StylometryPipeline and CLI runner."""
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from graph.repository import ThreatGraphRepository
from main import app
from pipeline import StylometryPipeline
from schemas.raw_post import RawForumPost

runner = CliRunner()


@pytest.fixture
def repo(tmp_path):
    """Clean repository fixture with temp-isolated storage."""
    temp_store = str(tmp_path / "graph_store_test.json")
    repository = ThreatGraphRepository(store_path=temp_store)
    repository.clear()
    return repository


@pytest.fixture
def pipeline(repo):
    """Pipeline instance using isolated repository."""
    return StylometryPipeline(repository=repo)


def test_pipeline_process_single_post(pipeline):
    """Verify single post processing extracts features, indicators, and persists into repository."""
    post = RawForumPost(
        post_id="test_pipe_001",
        forum_name="DreadClone",
        author_handle="ShadowBroker",
        raw_content="Exclusive exploit package. Contact via BTC bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s or PGP.",
    )

    profile = pipeline.process_post(post)

    assert profile.handle == "ShadowBroker"
    assert profile.platform == "DreadClone"
    assert profile.attribution_id is not None
    assert len(profile.identifiers.crypto_wallets) >= 1
    assert profile.identifiers.crypto_wallets[0].currency == "BTC"
    assert profile.features.character_count > 0

    # Verify presence in repository candidate profiles
    candidates = pipeline.repository.get_candidate_profiles()
    assert len(candidates) == 1
    assert candidates[0].handle == "ShadowBroker"


def test_pipeline_process_batch_links_personas(pipeline, sample_posts):
    """Verify that batch processing links Persona A and Persona C into the same cluster."""
    # Select posts from ShadowBroker (Persona A) and GhostMigrant (Persona C)
    actor_a_posts = [p for p in sample_posts if p.author_handle == "ShadowBroker"]
    actor_c_posts = [p for p in sample_posts if p.author_handle == "GhostMigrant"]

    target_posts = actor_a_posts + actor_c_posts
    processed = pipeline.process_batch(target_posts)

    assert len(processed) == len(target_posts)

    # Check that both personas share the same attribution_id
    candidates = pipeline.repository.get_candidate_profiles()
    sb_profile = next(p for p in candidates if p.handle == "ShadowBroker")
    gm_profile = next(p for p in candidates if p.handle == "GhostMigrant")

    assert sb_profile.attribution_id is not None
    assert gm_profile.attribution_id is not None
    assert sb_profile.attribution_id == gm_profile.attribution_id

    # Verify actor network query
    actor_id = sb_profile.attribution_id
    network = pipeline.repository.query_actor_network(actor_id)
    handles = {h["handle"] for h in network["handles"]}
    assert handles == {"ShadowBroker", "GhostMigrant"}
    assert set(network["marketplaces"]) == {"AlphaVendor", "DreadClone"}
    assert network["attribution_confidence"] >= 0.80
    assert len(network["linkages"]) >= 1


def test_pipeline_isolates_unrelated_personas(pipeline, sample_posts):
    """Verify Persona B (CryptoRebel) and Persona D (ScriptKiddie) do NOT link to Persona A."""
    posts_a = [p for p in sample_posts if p.author_handle == "ShadowBroker"][:2]
    posts_b = [p for p in sample_posts if p.author_handle == "CryptoRebel"][:2]
    posts_d = [p for p in sample_posts if p.author_handle == "ScriptKiddie"][:2]

    pipeline.process_batch(posts_a + posts_b + posts_d)

    candidates = pipeline.repository.get_candidate_profiles()
    sb = next(p for p in candidates if p.handle == "ShadowBroker")
    cr = next(p for p in candidates if p.handle == "CryptoRebel")
    sk = next(p for p in candidates if p.handle == "ScriptKiddie")

    # All 3 personas must have distinct attribution cluster IDs
    assert sb.attribution_id != cr.attribution_id
    assert sb.attribution_id != sk.attribution_id
    assert cr.attribution_id != sk.attribution_id


def test_cli_ingest_fixtures_command():
    """Verify CLI command 'ingest-fixtures' executes successfully with exit code 0."""
    runner.invoke(app, ["init-db", "--clear"])
    result = runner.invoke(app, ["ingest-fixtures", "--fixtures", "fixtures/sample_posts.json"])
    assert result.exit_code == 0
    assert "Successfully ingested 24 posts end-to-end!" in result.stdout
    assert "Distinct Personas: 4" in result.stdout
    assert "Resolved Threat Actor Clusters: 3" in result.stdout


def test_cli_export_actor_command(tmp_path):
    """Verify CLI command 'export-actor' outputs JSON and CSV deliverables."""
    out_dir = str(tmp_path / "exports_test")
    # Clear and ingest fixtures
    runner.invoke(app, ["init-db", "--clear"])
    runner.invoke(app, ["ingest-fixtures", "--fixtures", "fixtures/sample_posts.json"])

    # Retrieve resolved cluster ID for ShadowBroker
    repo = ThreatGraphRepository()
    candidates = repo.get_candidate_profiles()
    sb = next(p for p in candidates if p.handle == "ShadowBroker")
    actor_id = sb.attribution_id
    assert actor_id is not None

    # Export actor
    result = runner.invoke(
        app,
        ["export-actor", "--actor-id", actor_id, "--format", "both", "--output-dir", out_dir],
    )
    assert result.exit_code == 0
    assert "Threat Actor Briefing Summary:" in result.stdout
    assert "GhostMigrant" in result.stdout
    assert "ShadowBroker" in result.stdout

    # Verify physical file creation
    json_path = Path(out_dir) / f"{actor_id}.json"
    csv_path = Path(out_dir) / f"{actor_id}.csv"
    assert json_path.exists()
    assert csv_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["root_actor_id"] == actor_id
    assert "GhostMigrant" in data["alias_handles"]
    assert "ShadowBroker" in data["alias_handles"]


def test_cli_run_worker_once(tmp_path):
    """Verify CLI worker polls incoming directory, ingests posts, and archives files."""
    in_dir = tmp_path / "incoming"
    proc_dir = tmp_path / "processed"
    in_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    sample_post_data = [
        {
            "record_id": "worker-post-001",
            "marketplace": "AlphaVendor",
            "actor_handle": "WorkerTestActor",
            "raw_text": "Incoming post from worker directory. Payment in BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa.",
        }
    ]
    test_batch_file = in_dir / "incoming_batch_01.json"
    with open(test_batch_file, "w", encoding="utf-8") as f:
        json.dump(sample_post_data, f)

    result = runner.invoke(
        app,
        [
            "run-worker",
            "--input-dir",
            str(in_dir),
            "--processed-dir",
            str(proc_dir),
            "--once",
        ],
    )
    assert result.exit_code == 0
    # Original incoming file moved to processed
    assert not test_batch_file.exists()
    assert (proc_dir / "incoming_batch_01.json").exists()
