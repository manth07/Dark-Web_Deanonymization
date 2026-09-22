"""Unified processing pipeline orchestrating NLP extraction, vector embeddings, entity resolution, and Neo4j graph persistence."""
import hashlib
from typing import List, Optional

from ai.entity_resolution import EntityResolver, LinkageDecision
from ai.ollama_client import OllamaStylometryService
from core.logger import get_logger
from graph.repository import ThreatGraphRepository
from nlp.identifier_extractor import IdentifierExtractor
from nlp.stylometry import StylometryExtractor
from schemas.extracted_features import ThreatActorProfile
from schemas.raw_post import RawForumPost

logger = get_logger("pipeline")


class StylometryPipeline:
    """Core processing pipeline connecting extraction, AI embeddings, entity resolution, and graph persistence."""

    def __init__(
        self,
        stylometry_extractor: Optional[StylometryExtractor] = None,
        identifier_extractor: Optional[IdentifierExtractor] = None,
        ollama_service: Optional[OllamaStylometryService] = None,
        entity_resolver: Optional[EntityResolver] = None,
        repository: Optional[ThreatGraphRepository] = None,
    ) -> None:
        self.stylometry_extractor = stylometry_extractor or StylometryExtractor()
        self.identifier_extractor = identifier_extractor or IdentifierExtractor()
        self.ollama_service = ollama_service or OllamaStylometryService()
        self.entity_resolver = entity_resolver or EntityResolver(ollama_service=self.ollama_service)
        self.repository = repository or ThreatGraphRepository()

    def process_post(self, post: RawForumPost) -> ThreatActorProfile:
        """Process a single dark web forum post end-to-end.

        1. Extract classical stylometric features (sentence length, word length, TTR, punctuation).
        2. Extract crypto wallets (BTC, XMR, ETH), PGP keys/fingerprints, and IPs.
        3. Generate text embedding vector via Ollama.
        4. Query existing candidate profiles from Neo4j graph repository.
        5. Execute EntityResolver to determine if this persona matches an existing threat actor cluster.
        6. Persist results into Neo4j using ThreatGraphRepository.
        """
        # 1. Classical stylometric features
        features = self.stylometry_extractor.extract_features(post.raw_content)

        # 2. Extract technical and cryptographic identifiers
        identifiers = self.identifier_extractor.extract_all(post.raw_content)

        # 3. Generate dense semantic embedding via Ollama
        try:
            embedding = self.ollama_service.generate_embedding(post.raw_content)
            features.embedding = embedding
        except Exception as exc:
            logger.warning(f"Embedding generation failed for post '{post.post_id}': {exc}")
            features.embedding = []

        # 4. Construct candidate ThreatActorProfile
        candidate = ThreatActorProfile(
            handle=post.author_handle,
            platform=post.forum_name,
            features=features,
            identifiers=identifiers,
        )

        # Query existing candidate profiles from Neo4j / graph store
        candidate_profiles = self.repository.get_candidate_profiles()

        # Check if this exact handle/platform already has an attribution cluster in the graph
        existing_self = next(
            (
                p
                for p in candidate_profiles
                if p.handle == candidate.handle
                and p.platform == candidate.platform
                and p.attribution_id
            ),
            None,
        )
        if existing_self and existing_self.attribution_id:
            candidate.attribution_id = existing_self.attribution_id

        # 5. Execute EntityResolver
        decision: LinkageDecision = self.entity_resolver.resolve_profile(
            candidate, candidate_profiles
        )

        candidate_key = {"handle": candidate.handle, "platform": candidate.platform}

        if decision.matched and decision.target_handle:
            candidate.attribution_id = decision.canonical_actor_id
            target_profile = next(
                (p for p in candidate_profiles if p.handle == decision.target_handle),
                None,
            )
            target_platform = target_profile.platform if target_profile else post.forum_name
            target_key = {"handle": decision.target_handle, "platform": target_platform}

            # Persist attribution link and CONTROLS relationships
            self.repository.create_attribution_link(
                actor_id=decision.canonical_actor_id,
                persona_a_key=candidate_key,
                persona_b_key=target_key,
                confidence=decision.confidence_score,
                reasons=decision.link_reasons,
            )
            logger.info(
                f"[ATTRIBUTION MATCH] Linked persona '{candidate.handle}' on '{candidate.platform}' "
                f"to '{decision.target_handle}' on '{target_platform}' "
                f"(Actor: '{decision.canonical_actor_id}', Confidence: {decision.confidence_score:.2f}, "
                f"Reasons: {decision.link_reasons})"
            )
        else:
            if not candidate.attribution_id:
                candidate.attribution_id = f"actor-{hashlib.md5(f'{candidate.handle}:{candidate.platform}'.encode()).hexdigest()[:8]}"
                self.repository.link_persona_to_actor(
                    actor_id=candidate.attribution_id,
                    persona_key=candidate_key,
                    confidence=1.0,
                )
                logger.info(
                    f"[NEW ACTOR CLUSTER] Registered persona '{candidate.handle}' on '{candidate.platform}' "
                    f"under new cluster '{candidate.attribution_id}'"
                )

        # 6. Persist persona and post in repository
        self.repository.upsert_persona(candidate, post)

        # Log extracted indicators
        if candidate.identifiers.crypto_wallets:
            wallets_str = [
                f"{w.currency}:{w.address}" for w in candidate.identifiers.crypto_wallets
            ]
            logger.info(f"[{post.post_id}] Extracted {len(wallets_str)} wallet(s): {wallets_str}")

        if candidate.identifiers.pgp_keys:
            logger.info(f"[{post.post_id}] Extracted {len(candidate.identifiers.pgp_keys)} PGP key(s)")

        if candidate.identifiers.ip_addresses:
            logger.info(
                f"[{post.post_id}] Extracted {len(candidate.identifiers.ip_addresses)} IP(s): "
                f"{candidate.identifiers.ip_addresses}"
            )

        return candidate

    def process_batch(self, posts: List[RawForumPost]) -> List[ThreatActorProfile]:
        """Process a stream of raw posts with structured logging and progress tracking."""
        total = len(posts)
        logger.info(f"Starting ingestion batch of {total} forum posts...")
        processed_profiles: List[ThreatActorProfile] = []

        for idx, post in enumerate(posts, start=1):
            try:
                profile = self.process_post(post)
                processed_profiles.append(profile)
                if idx % 6 == 0 or idx == total:
                    logger.info(f"Progress: [{idx}/{total}] posts processed ({idx / total * 100:.1f}%)")
            except Exception as exc:
                logger.error(f"Error processing post '{post.post_id}': {exc}", exc_info=True)
                raise

        logger.info(f"Completed ingestion batch of {len(processed_profiles)} posts successfully.")
        return processed_profiles
