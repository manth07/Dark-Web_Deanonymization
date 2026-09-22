"""Unit tests for Ollama AI embedding and stylometric profiling service."""
import pytest
import numpy as np

from ai.ollama_client import OllamaStylometryService


@pytest.fixture
def mock_service() -> OllamaStylometryService:
    """Fixture providing OllamaStylometryService in explicit mock mode."""
    return OllamaStylometryService(mock=True, embedding_dim=768)


def test_embedding_dimension_consistency(mock_service: OllamaStylometryService):
    """Verify generated embeddings have consistent dimension and unit normalization."""
    texts = [
        "NEW DUMP... ESCROW ONLY... BTC REQUIRED...",
        "The epistemological hegemony of centralized panoptic surveillance...",
        "yo bro check this out lmao fresh leaks fire!!",
        "Short text.",
    ]

    for t in texts:
        vec = mock_service.generate_embedding(t)
        assert len(vec) == 768
        # Unit normalization: norm should be ~1.0
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-4


def test_embedding_deterministic_reproducibility(mock_service: OllamaStylometryService):
    """Verify identical text produces identical embedding in mock mode."""
    text = "DATABASE ACCESS AVAILABLE... CONTACT VIA PGP..."
    vec1 = mock_service.generate_embedding(text)
    vec2 = mock_service.generate_embedding(text)

    assert vec1 == vec2
    sim = mock_service.compute_similarity(vec1, vec2)
    assert abs(sim - 1.0) < 1e-6


def test_cosine_similarity_edge_cases(mock_service: OllamaStylometryService):
    """Verify cosine similarity on identical, orthogonal, opposite, and zero vectors."""
    # 1. Identical vectors
    v1 = [1.0, 0.0, 0.0, 0.0]
    assert abs(mock_service.compute_similarity(v1, v1) - 1.0) < 1e-6

    # 2. Orthogonal vectors
    v_ortho = [0.0, 1.0, 0.0, 0.0]
    assert abs(mock_service.compute_similarity(v1, v_ortho)) < 1e-6

    # 3. Opposite vectors
    v_opp = [-1.0, 0.0, 0.0, 0.0]
    assert abs(mock_service.compute_similarity(v1, v_opp) - (-1.0)) < 1e-6

    # 4. Zero vector handled gracefully per Error_Handling.md
    v_zero = [0.0, 0.0, 0.0, 0.0]
    assert mock_service.compute_similarity(v1, v_zero) == 0.0
    assert mock_service.compute_similarity(v_zero, v_zero) == 0.0

    # 5. Empty vector or dimension mismatch
    assert mock_service.compute_similarity([], v1) == 0.0
    assert mock_service.compute_similarity(v1, [1.0, 2.0]) == 0.0


def test_strip_overt_identifiers(mock_service: OllamaStylometryService):
    """Verify overt technical indicators are stripped before embedding generation."""
    sample_text = (
        "NEW DUMP... ESCROW ONLY... BTC: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq... "
        "OR XMR: 44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otKEfZagUopA9996oReoStZ6CHngAoRMa25VrWAFGLvmjh2QW51Uv... "
        "OR ETH: 0x71C7656EC7ab88b098defB751B7401B5f6d8976F... "
        "TEST SERVER: 198.51.100.23... "
        "ONION LINK: http://dreadclone.onion/thread/99... "
        "PGP: 4A5B6C7D8E9F0A1B2C3D4E5F6A7B8C9D0E1F2A3B... "
        "CONTACT @vendor_shadow FOR DEALS!"
    )

    cleaned = mock_service.strip_overt_identifiers(sample_text)

    # Identifiers must not be present
    assert "bc1q" not in cleaned
    assert "44AFF" not in cleaned
    assert "0x71C" not in cleaned
    assert "198.51.100.23" not in cleaned
    assert "dreadclone.onion" not in cleaned
    assert "4A5B6C7D8E9F" not in cleaned
    assert "@vendor_shadow" not in cleaned

    # Core linguistic words and punctuation must be preserved
    assert "NEW DUMP" in cleaned
    assert "ESCROW ONLY" in cleaned
    assert "..." in cleaned


def test_fallback_mock_when_daemon_offline():
    """Verify service falls back to deterministic mock when connecting to an unreachable port."""
    # Use invalid local port where no service is listening
    unreachable_service = OllamaStylometryService(
        base_url="http://127.0.0.1:59999",
        mock=False,
        timeout=0.2,
    )

    # Should not crash, should fall back to mock embedding
    vec = unreachable_service.generate_embedding("Test resilient fallback embedding generation")
    assert len(vec) == 768
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-4


def test_stylistic_profile_summary(mock_service: OllamaStylometryService):
    """Verify stylistic profile summary generation from text samples."""
    samples = [
        "NEW SQL LEAK... 50K ACCOUNTS READY... NO TIME WASTERS...",
        "CREDENTIALS VERIFIED... ESCROW ONLY... FAST DEAL GUARANTEED...",
    ]

    summary = mock_service.generate_stylistic_profile_summary(samples)
    assert "Threat Actor Stylistic Profile" in summary
    assert "clipped sentence cadence" in summary
    assert "Analyzed Samples: 2" in summary
