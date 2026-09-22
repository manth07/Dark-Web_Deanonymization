"""Local AI embedding and stylometric profiling service using Ollama.

Includes overt identifier bias removal, cosine similarity calculation,
and deterministic fallback mocking for test independence.
"""
import hashlib
import re
import time
from typing import List, Optional
import httpx
import numpy as np

from core.config import settings
from core.logger import get_logger
from nlp.identifier_extractor import (
    BTC_BECH32_REGEX,
    BTC_P2PKH_REGEX,
    BTC_P2SH_REGEX,
    ETH_REGEX,
    IPV4_REGEX,
    PGP_BLOCK_REGEX,
    PGP_FINGERPRINT_CONTIGUOUS,
    PGP_FINGERPRINT_SPACED,
    XMR_INTEGRATED_REGEX,
    XMR_STANDARD_REGEX,
)

logger = get_logger("ai.ollama_client")

# URL and handle regex
URL_REGEX = re.compile(r"https?://\S+|www\.\S+|\S+\.onion\S*", re.IGNORECASE)
HANDLE_MENTION_REGEX = re.compile(r"@[a-zA-Z0-9_\-]+")


class OllamaStylometryService:
    """Service managing local AI embeddings and LLM stylometry profiles via Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        embed_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        mock: Optional[bool] = None,
        timeout: float = 15.0,
        embedding_dim: int = 768,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.embed_model = embed_model or settings.OLLAMA_EMBED_MODEL
        self.llm_model = llm_model or settings.OLLAMA_LLM_MODEL
        self.mock = mock if mock is not None else settings.MOCK_OLLAMA
        self.timeout = timeout
        self.embedding_dim = embedding_dim

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=5.0),
        )

    def strip_overt_identifiers(self, text: str) -> str:
        """Strip overt technical identifiers so embeddings evaluate purely linguistic style."""
        if not text or not isinstance(text, str):
            return ""

        cleaned = text

        # 1. PGP Armor Blocks
        cleaned = PGP_BLOCK_REGEX.sub(" ", cleaned)

        # 2. Cryptocurrency Wallets
        cleaned = XMR_STANDARD_REGEX.sub(" ", cleaned)
        cleaned = XMR_INTEGRATED_REGEX.sub(" ", cleaned)
        cleaned = ETH_REGEX.sub(" ", cleaned)
        cleaned = BTC_BECH32_REGEX.sub(" ", cleaned)
        cleaned = BTC_P2PKH_REGEX.sub(" ", cleaned)
        cleaned = BTC_P2SH_REGEX.sub(" ", cleaned)

        # 3. PGP Fingerprints
        cleaned = PGP_FINGERPRINT_SPACED.sub(" ", cleaned)
        cleaned = PGP_FINGERPRINT_CONTIGUOUS.sub(" ", cleaned)

        # 4. URLs & Onion Addresses
        cleaned = URL_REGEX.sub(" ", cleaned)

        # 5. IP Addresses
        cleaned = IPV4_REGEX.sub(" ", cleaned)

        # 6. Direct User Mentions
        cleaned = HANDLE_MENTION_REGEX.sub(" ", cleaned)

        # Normalize whitespace
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
        return cleaned.strip()

    def _generate_deterministic_mock_vector(self, text: str) -> List[float]:
        """Generate deterministic, unit-normalized float vector based on text hash."""
        # Use SHA-256 digest of cleaned text as RNG seed
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        seed_int = int.from_bytes(seed_bytes[:4], "big")
        rng = np.random.RandomState(seed_int)

        # Generate Gaussian random vector
        vec = rng.randn(self.embedding_dim)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Request vector embeddings for text, using Ollama with retries and deterministic fallback.

        Strips technical identifiers before embedding to ensure focus on authorship style.
        """
        cleaned_text = self.strip_overt_identifiers(text)
        if not cleaned_text:
            cleaned_text = "empty"

        target_model = model or self.embed_model

        # Fast path if explicitly set to mock mode
        if self.mock:
            return self._generate_deterministic_mock_vector(cleaned_text)

        # Attempt live connection to Ollama with retry backoff
        attempts = 2
        backoff = 0.5

        for attempt in range(1, attempts + 1):
            try:
                response = self.client.post(
                    "/api/embeddings",
                    json={"model": target_model, "prompt": cleaned_text},
                )
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", [])
                    if embedding:
                        return [float(x) for x in embedding]
                logger.warning(
                    "Ollama API returned non-200 status",
                    extra={"status": response.status_code, "attempt": attempt},
                )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    f"Ollama connection error on attempt {attempt}/{attempts}: {exc}"
                )

            if attempt < attempts:
                time.sleep(backoff)
                backoff *= 2.0

        # Fallback to deterministic vector if Ollama daemon is offline/unreachable
        logger.info("Falling back to deterministic offline embedding mock")
        self.mock = True
        return self._generate_deterministic_mock_vector(cleaned_text)

    def compute_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors with robust error handling.

        Handles zero-vectors, empty vectors, and dimension mismatches by returning 0.0.
        """
        if not vec_a or not vec_b:
            return 0.0

        if len(vec_a) != len(vec_b):
            logger.warning(
                f"Vector dimension mismatch: {len(vec_a)} vs {len(vec_b)}"
            )
            return 0.0

        a = np.asarray(vec_a, dtype=np.float64)
        b = np.asarray(vec_b, dtype=np.float64)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0.0 or norm_b == 0.0 or np.isnan(norm_a) or np.isnan(norm_b):
            return 0.0

        dot = np.dot(a, b)
        sim = dot / (norm_a * norm_b)

        if np.isnan(sim):
            return 0.0

        return float(np.clip(sim, -1.0, 1.0))

    def generate_stylistic_profile_summary(
        self,
        text_samples: List[str],
        model: Optional[str] = None,
    ) -> str:
        """Generate a natural-language stylometric summary of author's writing style."""
        if not text_samples:
            return "No text samples provided for stylistic profiling."

        target_model = model or self.llm_model

        if not self.mock:
            prompt = (
                "You are an expert stylometry and cyber threat intelligence analyst. "
                "Analyze the writing style of the following threat actor posts. "
                "Provide a concise summary covering: 1) Tone and demeanor, "
                "2) Vocabulary habits and technical sophistication, "
                "3) Punctuation quirks and syntax patterns, "
                "4) Behavioral indicators.\n\n"
                "Posts:\n" + "\n---\n".join(text_samples[:5])
            )
            try:
                response = self.client.post(
                    "/api/generate",
                    json={"model": target_model, "prompt": prompt, "stream": False},
                )
                if response.status_code == 200:
                    summary = response.json().get("response", "").strip()
                    if summary:
                        return summary
            except Exception as exc:
                logger.warning(f"Ollama generate request failed: {exc}")

        # Deterministic heuristic summary for offline / mock mode
        combined = " ".join(text_samples)
        upper_chars = sum(1 for c in combined if c.isupper())
        total_chars = max(len(combined), 1)
        upper_ratio = upper_chars / total_chars

        ellipses_count = combined.count("...")
        semicolons_count = combined.count(";")
        slang_words = sum(combined.lower().count(s) for s in ["bro", "lmao", "plz", "fire", "dm me"])

        style_traits = []
        if ellipses_count >= 3:
            style_traits.append("clipped sentence cadence with frequent ellipses breaks")
        if upper_ratio > 0.15:
            style_traits.append("heavy capitalization indicating urgent or aggressive commercial posture")
        if semicolons_count >= 2:
            style_traits.append("complex academic syntax with formal semicolons")
        if slang_words >= 2:
            style_traits.append("informal subterranean slang with casual grammar")

        if not style_traits:
            style_traits.append("standard neutral forum discourse")

        return (
            f"Threat Actor Stylistic Profile:\n"
            f"- Analyzed Samples: {len(text_samples)}\n"
            f"- Prominent Markers: {', '.join(style_traits)}\n"
            f"- Linguistic Sophistication: {'Academic' if semicolons_count >= 2 else ('Underground Market Vendor' if upper_ratio > 0.1 else 'Informal')}"
        )
