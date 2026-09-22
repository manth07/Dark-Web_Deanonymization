"""Multi-factor Entity Resolution Engine for dark web threat actor deanonymization.

Combines hard cryptographic/infrastructure identifiers with dense AI embeddings,
classical NLP stylometry, and vocabulary distributions to link aliases across forums.
"""
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field

from ai.ollama_client import OllamaStylometryService
from core.config import settings
from core.logger import get_logger
from schemas.extracted_features import StylometricFeatures, ThreatActorProfile

logger = get_logger("ai.entity_resolution")


class LinkageDecision(BaseModel):
    """Detailed resolution decision linking a candidate profile to an existing persona/actor."""

    model_config = ConfigDict(extra="ignore")

    matched: bool = Field(..., description="Whether attribution confidence meets or exceeds threshold")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Normalized attribution confidence (0.0 - 1.0)")
    link_reasons: List[str] = Field(default_factory=list, description="Audit trail of contributing evidence")
    canonical_actor_id: str = Field(..., description="Resolved root ThreatActor cluster identifier")
    candidate_handle: str = Field(..., description="Candidate persona username")
    target_handle: Optional[str] = Field(default=None, description="Matched existing persona handle")
    component_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Sub-scores for hard indicators, semantic vector, classical stylometry, and topic",
    )


class EntityResolver:
    """Resolves identities and links candidate personas using weighted multi-factor attribution."""

    def __init__(
        self,
        threshold: Optional[float] = None,
        ollama_service: Optional[OllamaStylometryService] = None,
    ) -> None:
        self.threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        self.ollama_service = ollama_service or OllamaStylometryService()

    def _calculate_classical_similarity(
        self,
        f_cand: StylometricFeatures,
        f_target: StylometricFeatures,
    ) -> float:
        """Calculate normalized similarity across lexical, syntactic, and structural metrics."""
        # 1. Sentence length similarity (tolerance up to 15 words difference)
        sent_diff = abs(f_cand.average_sentence_length - f_target.average_sentence_length)
        sent_sim = max(0.0, 1.0 - (sent_diff / 15.0))

        # 2. Uppercase ratio similarity
        upper_diff = abs(f_cand.uppercase_ratio - f_target.uppercase_ratio)
        upper_sim = max(0.0, 1.0 - (upper_diff / 0.5))

        # 3. Punctuation frequency overlap
        p_cand = f_cand.punctuation_frequency
        p_target = f_target.punctuation_frequency
        all_punct = set(p_cand.keys()) | set(p_target.keys())

        if all_punct:
            dot_product = sum(p_cand.get(k, 0) * p_target.get(k, 0) for k in all_punct)
            norm_c = sum(v ** 2 for v in p_cand.values()) ** 0.5
            norm_t = sum(v ** 2 for v in p_target.values()) ** 0.5
            punct_sim = dot_product / (norm_c * norm_t) if norm_c > 0 and norm_t > 0 else 0.0
        else:
            punct_sim = 1.0 if not p_cand and not p_target else 0.0

        # Special bonus if both utilize characteristic ellipses habits
        if p_cand.get("...", 0) >= 2 and p_target.get("...", 0) >= 2:
            punct_sim = min(1.0, punct_sim + 0.15)

        # 4. Type-Token Ratio similarity
        ttr_diff = abs(f_cand.type_token_ratio - f_target.type_token_ratio)
        ttr_sim = max(0.0, 1.0 - ttr_diff)

        # Weighted blend of classical stylometric factors
        classical_score = (
            0.35 * sent_sim
            + 0.30 * upper_sim
            + 0.25 * punct_sim
            + 0.10 * ttr_sim
        )
        return max(0.0, min(1.0, round(classical_score, 4)))

    def _calculate_topic_similarity(
        self,
        f_cand: StylometricFeatures,
        f_target: StylometricFeatures,
    ) -> float:
        """Calculate vocabulary and function word distribution similarity."""
        fw_cand = f_cand.function_word_frequency
        fw_target = f_target.function_word_frequency
        all_fw = set(fw_cand.keys()) | set(fw_target.keys())

        if not all_fw:
            return 0.5

        dot_product = sum(fw_cand.get(k, 0.0) * fw_target.get(k, 0.0) for k in all_fw)
        norm_c = sum(v ** 2 for v in fw_cand.values()) ** 0.5
        norm_t = sum(v ** 2 for v in fw_target.values()) ** 0.5

        if norm_c > 0 and norm_t > 0:
            sim = dot_product / (norm_c * norm_t)
            return max(0.0, min(1.0, round(sim, 4)))
        return 0.5

    def compare_profiles(
        self,
        candidate: ThreatActorProfile,
        target: ThreatActorProfile,
    ) -> LinkageDecision:
        """Compare a candidate profile against an existing profile and compute attribution confidence."""
        reasons: List[str] = []
        component_scores: Dict[str, float] = {}

        # 1. Hard Identifiers (Shared Wallets, Shared PGP, Shared IPs)
        cand_wallets = {(w.currency, w.address) for w in candidate.identifiers.crypto_wallets}
        target_wallets = {(w.currency, w.address) for w in target.identifiers.crypto_wallets}
        shared_wallets = cand_wallets & target_wallets

        cand_pgp = set(candidate.identifiers.pgp_keys)
        target_pgp = set(target.identifiers.pgp_keys)
        shared_pgp = cand_pgp & target_pgp

        cand_ips = set(candidate.identifiers.ip_addresses)
        target_ips = set(target.identifiers.ip_addresses)
        shared_ips = cand_ips & target_ips

        hard_matches_count = len(shared_wallets) + len(shared_pgp) + len(shared_ips)

        if shared_wallets:
            for curr, addr in shared_wallets:
                reasons.append(f"Exact shared cryptocurrency wallet ({curr}: {addr})")
        if shared_pgp:
            for key in shared_pgp:
                summary_key = key[:20] + "..." if len(key) > 20 else key
                reasons.append(f"Shared cryptographic PGP key/fingerprint ({summary_key})")
        if shared_ips:
            for ip in shared_ips:
                reasons.append(f"Shared infrastructure IP address ({ip})")

        hard_score = 0.0
        if hard_matches_count >= 2:
            hard_score = 1.0
        elif hard_matches_count == 1:
            hard_score = 0.95
        component_scores["hard_identifiers"] = hard_score

        # 2. Stylometric Vector Cosine Similarity (Weight: 0.50)
        vec_sim = 0.0
        if candidate.features.embedding and target.features.embedding:
            vec_sim = self.ollama_service.compute_similarity(
                candidate.features.embedding,
                target.features.embedding,
            )
        component_scores["semantic_vector_cosine"] = vec_sim
        if vec_sim >= 0.85:
            reasons.append(f"High stylometric semantic embedding similarity ({vec_sim:.2f})")

        # 3. Classical Stylometry Similarity (Weight: 0.30)
        classical_sim = self._calculate_classical_similarity(candidate.features, target.features)
        component_scores["classical_stylometry"] = classical_sim
        if classical_sim >= 0.75:
            reasons.append(f"Strong classical stylometric trait alignment (Cadence/Punctuation similarity: {classical_sim:.2f})")

        # 4. Topic / Function Word Similarity (Weight: 0.20)
        topic_sim = self._calculate_topic_similarity(candidate.features, target.features)
        component_scores["topic_language"] = topic_sim
        if topic_sim >= 0.70:
            reasons.append(f"Shared function word distribution and vocabulary habits ({topic_sim:.2f})")

        # Compute Weighted Soft Score
        vector_weight = 0.50
        classical_weight = 0.30
        topic_weight = 0.20

        # Effective vector factor
        vector_factor = vec_sim if vec_sim >= 0.85 else max(0.0, vec_sim * 0.7)
        soft_score = (
            vector_weight * vector_factor
            + classical_weight * classical_sim
            + topic_weight * topic_sim
        )
        component_scores["soft_score"] = round(soft_score, 4)

        # Final Confidence Aggregation
        if hard_score > 0.0:
            final_confidence = max(hard_score, soft_score)
        else:
            final_confidence = soft_score

        final_confidence = max(0.0, min(1.0, round(final_confidence, 4)))
        matched = final_confidence >= self.threshold

        # Canonical Actor ID resolution
        canonical_id = (
            target.attribution_id
            or candidate.attribution_id
            or f"actor-cluster-{hashlib.md5(min(candidate.handle, target.handle).encode()).hexdigest()[:8]}"
        )

        return LinkageDecision(
            matched=matched,
            confidence_score=final_confidence,
            link_reasons=reasons,
            canonical_actor_id=canonical_id,
            candidate_handle=candidate.handle,
            target_handle=target.handle,
            component_scores=component_scores,
        )

    def resolve_profile(
        self,
        candidate: ThreatActorProfile,
        existing_profiles: List[ThreatActorProfile],
    ) -> LinkageDecision:
        """Resolve a candidate profile against a collection of known profiles, picking the highest-confidence match."""
        if not existing_profiles:
            canonical_id = candidate.attribution_id or f"actor-cluster-{hashlib.md5(candidate.handle.encode()).hexdigest()[:8]}"
            return LinkageDecision(
                matched=False,
                confidence_score=0.0,
                link_reasons=["No existing profiles available for comparison"],
                canonical_actor_id=canonical_id,
                candidate_handle=candidate.handle,
                target_handle=None,
                component_scores={},
            )

        best_decision: Optional[LinkageDecision] = None

        for existing in existing_profiles:
            # Skip comparing profile with itself
            if existing.handle == candidate.handle and existing.platform == candidate.platform:
                continue

            decision = self.compare_profiles(candidate, existing)
            if best_decision is None or decision.confidence_score > best_decision.confidence_score:
                best_decision = decision

        if best_decision is None:
            canonical_id = candidate.attribution_id or f"actor-cluster-{hashlib.md5(candidate.handle.encode()).hexdigest()[:8]}"
            return LinkageDecision(
                matched=False,
                confidence_score=0.0,
                link_reasons=["No candidate match evaluated"],
                canonical_actor_id=canonical_id,
                candidate_handle=candidate.handle,
                target_handle=None,
                component_scores={},
            )

        return best_decision

    def cluster_profiles(
        self,
        profiles: List[ThreatActorProfile],
    ) -> Dict[str, List[ThreatActorProfile]]:
        """Cluster a collection of profiles into canonical actor groupings."""
        clusters: Dict[str, List[ThreatActorProfile]] = {}
        resolved_profiles: List[ThreatActorProfile] = []

        for p in profiles:
            if not resolved_profiles:
                cid = p.attribution_id or f"actor-cluster-{hashlib.md5(p.handle.encode()).hexdigest()[:8]}"
                p.attribution_id = cid
                clusters[cid] = [p]
                resolved_profiles.append(p)
                continue

            decision = self.resolve_profile(p, resolved_profiles)
            if decision.matched:
                cid = decision.canonical_actor_id
                p.attribution_id = cid
                if cid not in clusters:
                    clusters[cid] = []
                clusters[cid].append(p)
            else:
                cid = p.attribution_id or f"actor-cluster-{hashlib.md5(p.handle.encode()).hexdigest()[:8]}"
                p.attribution_id = cid
                clusters[cid] = [p]

            resolved_profiles.append(p)

        return clusters
