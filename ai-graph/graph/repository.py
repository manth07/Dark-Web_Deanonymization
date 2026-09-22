import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import settings
from core.logger import get_logger
from graph.driver import Neo4jDriver, get_neo4j_driver
from schemas.extracted_features import (
    CryptoWallet,
    ExtractedIdentifiers,
    StylometricFeatures,
    ThreatActorProfile,
)
from schemas.raw_post import RawForumPost

logger = get_logger("graph.repository")

# --- Cypher Query Templates ---

UPSERT_PERSONA_POST_QUERY = """
MERGE (p:Persona {handle: $handle, platform: $platform})
ON CREATE SET 
    p.first_seen = $timestamp,
    p.last_seen = $timestamp,
    p.avg_sentence_length = $avg_sentence_length,
    p.avg_word_length = $avg_word_length,
    p.type_token_ratio = $type_token_ratio,
    p.hapax_ratio = $hapax_ratio,
    p.paragraph_count = $paragraph_count,
    p.uppercase_ratio = $uppercase_ratio,
    p.character_count = $character_count
ON MATCH SET 
    p.last_seen = $timestamp,
    p.avg_sentence_length = $avg_sentence_length,
    p.avg_word_length = $avg_word_length,
    p.type_token_ratio = $type_token_ratio,
    p.hapax_ratio = $hapax_ratio,
    p.paragraph_count = $paragraph_count,
    p.uppercase_ratio = $uppercase_ratio,
    p.character_count = $character_count
MERGE (post:Post {post_id: $post_id})
ON CREATE SET 
    post.timestamp = $timestamp,
    post.forum_name = $platform,
    post.author_handle = $handle
MERGE (p)-[r:AUTHORED]->(post)
"""

LINK_CRYPTO_WALLET_QUERY = """
MERGE (p:Persona {handle: $handle, platform: $platform})
MERGE (w:CryptoWallet {address: $address})
ON CREATE SET w.currency = $currency
MERGE (p)-[r:UTILIZES_WALLET]->(w)
SET r.last_seen = $timestamp
"""

LINK_PGP_KEY_QUERY = """
MERGE (p:Persona {handle: $handle, platform: $platform})
MERGE (k:PGPKey {fingerprint: $fingerprint})
MERGE (p)-[r:OWNS_KEY]->(k)
SET r.last_seen = $timestamp
"""

LINK_IP_ADDRESS_QUERY = """
MERGE (p:Persona {handle: $handle, platform: $platform})
MERGE (i:IPAddress {ip: $ip})
MERGE (p)-[r:OBSERVED_IP]->(i)
SET r.last_seen = $timestamp
"""

CREATE_ATTRIBUTION_LINK_QUERY = """
MERGE (t:ThreatActor {actor_id: $actor_id})
ON CREATE SET t.attribution_confidence = $confidence, t.first_seen = $timestamp, t.last_seen = $timestamp
ON MATCH SET t.attribution_confidence = CASE WHEN $confidence > t.attribution_confidence THEN $confidence ELSE t.attribution_confidence END, t.last_seen = $timestamp

MERGE (p1:Persona {handle: $handle_a, platform: $platform_a})
MERGE (p2:Persona {handle: $handle_b, platform: $platform_b})

MERGE (t)-[c1:CONTROLS]->(p1)
SET c1.confidence = $confidence, c1.last_updated = $timestamp

MERGE (t)-[c2:CONTROLS]->(p2)
SET c2.confidence = $confidence, c2.last_updated = $timestamp

MERGE (p1)-[r:LINKED_TO {method: 'stylometry_v1'}]->(p2)
SET r.confidence = $confidence, r.reasons = $reasons, r.updated_at = $timestamp
"""

LINK_SINGLE_PERSONA_QUERY = """
MERGE (t:ThreatActor {actor_id: $actor_id})
ON CREATE SET t.attribution_confidence = $confidence, t.first_seen = $timestamp, t.last_seen = $timestamp
ON MATCH SET t.attribution_confidence = CASE WHEN $confidence > t.attribution_confidence THEN $confidence ELSE t.attribution_confidence END, t.last_seen = $timestamp

MERGE (p:Persona {handle: $handle, platform: $platform})
MERGE (t)-[c:CONTROLS]->(p)
SET c.confidence = $confidence, c.last_updated = $timestamp
"""

QUERY_ACTOR_NETWORK_QUERY = """
MATCH (t:ThreatActor {actor_id: $actor_id})
OPTIONAL MATCH (t)-[c:CONTROLS]->(p:Persona)
OPTIONAL MATCH (p)-[:AUTHORED]->(post:Post)
OPTIONAL MATCH (p)-[:UTILIZES_WALLET]->(w:CryptoWallet)
OPTIONAL MATCH (p)-[:OWNS_KEY]->(k:PGPKey)
OPTIONAL MATCH (p)-[:OBSERVED_IP]->(i:IPAddress)
OPTIONAL MATCH (p)-[link:LINKED_TO]->(target:Persona)
RETURN 
    t.actor_id AS actor_id,
    t.attribution_confidence AS attribution_confidence,
    collect(DISTINCT {handle: p.handle, platform: p.platform, first_seen: p.first_seen, last_seen: p.last_seen}) AS personas,
    collect(DISTINCT p.platform) AS marketplaces,
    collect(DISTINCT {address: w.address, currency: w.currency}) AS crypto_wallets,
    collect(DISTINCT k.fingerprint) AS pgp_keys,
    collect(DISTINCT i.ip) AS ip_addresses,
    collect(DISTINCT {post_id: post.post_id, timestamp: post.timestamp, handle: p.handle, platform: p.platform}) AS posts,
    collect(DISTINCT {
        source_handle: p.handle,
        source_platform: p.platform,
        target_handle: target.handle,
        target_platform: target.platform,
        confidence: link.confidence,
        reasons: link.reasons,
        method: link.method
    }) AS linkages
"""

GET_ALL_PROFILES_QUERY = """
MATCH (p:Persona)
OPTIONAL MATCH (t:ThreatActor)-[:CONTROLS]->(p)
OPTIONAL MATCH (p)-[:UTILIZES_WALLET]->(w:CryptoWallet)
OPTIONAL MATCH (p)-[:OWNS_KEY]->(k:PGPKey)
OPTIONAL MATCH (p)-[:OBSERVED_IP]->(i:IPAddress)
RETURN 
    p.handle AS handle,
    p.platform AS platform,
    t.actor_id AS attribution_id,
    p.avg_sentence_length AS avg_sentence_length,
    p.avg_word_length AS avg_word_length,
    p.type_token_ratio AS type_token_ratio,
    p.hapax_ratio AS hapax_ratio,
    p.paragraph_count AS paragraph_count,
    p.uppercase_ratio AS uppercase_ratio,
    p.character_count AS character_count,
    collect(DISTINCT {address: w.address, currency: w.currency}) AS crypto_wallets,
    collect(DISTINCT k.fingerprint) AS pgp_keys,
    collect(DISTINCT i.ip) AS ip_addresses
"""


class ThreatGraphRepository:
    """Repository service managing idempotent Cypher ingestion and graph queries."""

    def __init__(
        self,
        driver: Optional[Neo4jDriver] = None,
        store_path: Optional[str] = "data/graph_store.json",
    ) -> None:
        self.driver = driver or get_neo4j_driver()
        self.store_path = store_path
        self._is_connected_cache: Optional[bool] = None
        # In-memory graph structure ensuring full offline functionality and topological testing
        self._in_memory_store: Dict[str, Any] = {
            "threat_actors": {},
            "personas": {},
            "posts": {},
            "wallets": {},
            "pgp_keys": {},
            "ips": {},
            "controls": [],
            "authored": [],
            "utilizes_wallet": [],
            "owns_key": [],
            "observed_ip": [],
            "linked_to": [],
        }
        self._load_local_store()

    def _load_local_store(self) -> None:
        """Load in-memory graph store from disk if present."""
        if not self.store_path:
            return
        p = Path(self.store_path)
        if not p.exists():
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)

            personas = {}
            for k_str, val in data.get("personas", {}).items():
                parts = k_str.split("|||")
                key = (parts[0], parts[1]) if len(parts) == 2 else (k_str, "")
                if "features" in val and isinstance(val["features"], dict):
                    val["features"] = StylometricFeatures(**val["features"])
                personas[key] = val

            controls = [(item[0], tuple(item[1])) for item in data.get("controls", [])]
            authored = [(tuple(item[0]), item[1]) for item in data.get("authored", [])]
            utilizes_wallet = [(tuple(item[0]), item[1]) for item in data.get("utilizes_wallet", [])]
            owns_key = [(tuple(item[0]), item[1]) for item in data.get("owns_key", [])]
            observed_ip = [(tuple(item[0]), item[1]) for item in data.get("observed_ip", [])]

            linked_to = []
            for link in data.get("linked_to", []):
                linked_to.append({
                    "source": tuple(link["source"]),
                    "target": tuple(link["target"]),
                    "confidence": link["confidence"],
                    "reasons": link["reasons"],
                    "method": link["method"],
                    "updated_at": link.get("updated_at", ""),
                })

            self._in_memory_store = {
                "threat_actors": data.get("threat_actors", {}),
                "personas": personas,
                "posts": data.get("posts", {}),
                "wallets": data.get("wallets", {}),
                "pgp_keys": data.get("pgp_keys", {}),
                "ips": data.get("ips", {}),
                "controls": controls,
                "authored": authored,
                "utilizes_wallet": utilizes_wallet,
                "owns_key": owns_key,
                "observed_ip": observed_ip,
                "linked_to": linked_to,
            }
        except Exception as exc:
            logger.warning(f"Could not load local graph store from {self.store_path}: {exc}")

    def _save_local_store(self) -> None:
        """Persist in-memory graph store to disk."""
        if not self.store_path:
            return
        try:
            p = Path(self.store_path)
            p.parent.mkdir(parents=True, exist_ok=True)

            personas_ser = {}
            for key, val in self._in_memory_store["personas"].items():
                k_str = f"{key[0]}|||{key[1]}"
                v_copy = dict(val)
                if hasattr(v_copy.get("features"), "model_dump"):
                    v_copy["features"] = v_copy["features"].model_dump()
                personas_ser[k_str] = v_copy

            controls_ser = [[item[0], list(item[1])] for item in self._in_memory_store["controls"]]
            authored_ser = [[list(item[0]), item[1]] for item in self._in_memory_store["authored"]]
            wallets_ser = [[list(item[0]), item[1]] for item in self._in_memory_store["utilizes_wallet"]]
            owns_key_ser = [[list(item[0]), item[1]] for item in self._in_memory_store["owns_key"]]
            observed_ip_ser = [[list(item[0]), item[1]] for item in self._in_memory_store["observed_ip"]]

            linked_to_ser = []
            for link in self._in_memory_store["linked_to"]:
                linked_to_ser.append({
                    "source": list(link["source"]),
                    "target": list(link["target"]),
                    "confidence": link["confidence"],
                    "reasons": link["reasons"],
                    "method": link["method"],
                    "updated_at": link.get("updated_at", ""),
                })

            data = {
                "threat_actors": self._in_memory_store["threat_actors"],
                "personas": personas_ser,
                "posts": self._in_memory_store["posts"],
                "wallets": self._in_memory_store["wallets"],
                "pgp_keys": self._in_memory_store["pgp_keys"],
                "ips": self._in_memory_store["ips"],
                "controls": controls_ser,
                "authored": authored_ser,
                "utilizes_wallet": wallets_ser,
                "owns_key": owns_key_ser,
                "observed_ip": observed_ip_ser,
                "linked_to": linked_to_ser,
            }

            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.warning(f"Could not persist local graph store to {self.store_path}: {exc}")

    def _is_live_driver(self) -> bool:
        """Check if driver is active, connected, or a test mock."""
        if self.driver is None:
            return False
        # If driver has an execute_write mock or test override
        if hasattr(self.driver, "execute_write") and type(self.driver) != Neo4jDriver:
            return True
        if settings.MOCK_NEO4J:
            return False
        if self._is_connected_cache is not None:
            return self._is_connected_cache
        self._is_connected_cache = self.driver.verify_connectivity()
        return self._is_connected_cache

    def upsert_persona(self, profile: ThreatActorProfile, post: RawForumPost) -> None:
        """Idempotently insert/update Persona, Post, Identifiers, and Stylometry metadata.

        Creates nodes and edges for:
        - (:Persona {handle, platform})
        - (:Post {post_id})
        - (:Persona)-[:AUTHORED]->(:Post)
        - (:Persona)-[:UTILIZES_WALLET]->(:CryptoWallet)
        - (:Persona)-[:OWNS_KEY]->(:PGPKey)
        - (:Persona)-[:OBSERVED_IP]->(:IPAddress)
        """
        timestamp_str = (
            post.timestamp.isoformat()
            if hasattr(post.timestamp, "isoformat")
            else str(post.timestamp)
        )
        persona_key = (profile.handle, profile.platform)

        # 1. Update in-memory graph store
        if persona_key not in self._in_memory_store["personas"]:
            self._in_memory_store["personas"][persona_key] = {
                "handle": profile.handle,
                "platform": profile.platform,
                "first_seen": timestamp_str,
                "last_seen": timestamp_str,
                "features": profile.features,
                "attribution_id": profile.attribution_id,
            }
        else:
            self._in_memory_store["personas"][persona_key]["last_seen"] = timestamp_str
            self._in_memory_store["personas"][persona_key]["features"] = profile.features
            if profile.attribution_id:
                self._in_memory_store["personas"][persona_key]["attribution_id"] = profile.attribution_id

        # Post node
        self._in_memory_store["posts"][post.post_id] = {
            "post_id": post.post_id,
            "timestamp": timestamp_str,
            "forum_name": profile.platform,
            "author_handle": profile.handle,
        }

        # AUTHORED edge
        authored_edge = (persona_key, post.post_id)
        if authored_edge not in self._in_memory_store["authored"]:
            self._in_memory_store["authored"].append(authored_edge)

        # Wallets
        for wallet in profile.identifiers.crypto_wallets:
            self._in_memory_store["wallets"][wallet.address] = {
                "address": wallet.address,
                "currency": wallet.currency,
            }
            wallet_edge = (persona_key, wallet.address)
            if wallet_edge not in self._in_memory_store["utilizes_wallet"]:
                self._in_memory_store["utilizes_wallet"].append(wallet_edge)

        # PGP Keys
        for pgp in profile.identifiers.pgp_keys:
            self._in_memory_store["pgp_keys"][pgp] = {"fingerprint": pgp}
            pgp_edge = (persona_key, pgp)
            if pgp_edge not in self._in_memory_store["owns_key"]:
                self._in_memory_store["owns_key"].append(pgp_edge)

        # IP Addresses
        for ip in profile.identifiers.ip_addresses:
            self._in_memory_store["ips"][ip] = {"ip": ip}
            ip_edge = (persona_key, ip)
            if ip_edge not in self._in_memory_store["observed_ip"]:
                self._in_memory_store["observed_ip"].append(ip_edge)

        # 2. Execute Cypher queries on live driver / mock driver
        if self._is_live_driver():
            # A. Persona + Post + AUTHORED + Stylometry
            post_params = {
                "handle": profile.handle,
                "platform": profile.platform,
                "post_id": post.post_id,
                "timestamp": timestamp_str,
                "avg_sentence_length": float(profile.features.average_sentence_length),
                "avg_word_length": float(profile.features.average_word_length),
                "type_token_ratio": float(profile.features.type_token_ratio),
                "hapax_ratio": float(profile.features.hapax_legomena_ratio),
                "paragraph_count": int(profile.features.paragraph_count),
                "uppercase_ratio": float(profile.features.uppercase_ratio),
                "character_count": int(profile.features.character_count),
            }
            self.driver.execute_write(UPSERT_PERSONA_POST_QUERY, post_params)

            # B. Wallets
            for wallet in profile.identifiers.crypto_wallets:
                wallet_params = {
                    "handle": profile.handle,
                    "platform": profile.platform,
                    "address": wallet.address,
                    "currency": wallet.currency,
                    "timestamp": timestamp_str,
                }
                self.driver.execute_write(LINK_CRYPTO_WALLET_QUERY, wallet_params)

            # C. PGP Keys
            for pgp in profile.identifiers.pgp_keys:
                pgp_params = {
                    "handle": profile.handle,
                    "platform": profile.platform,
                    "fingerprint": pgp,
                    "timestamp": timestamp_str,
                }
                self.driver.execute_write(LINK_PGP_KEY_QUERY, pgp_params)

            # D. IP Addresses
            for ip in profile.identifiers.ip_addresses:
                ip_params = {
                    "handle": profile.handle,
                    "platform": profile.platform,
                    "ip": ip,
                    "timestamp": timestamp_str,
                }
                self.driver.execute_write(LINK_IP_ADDRESS_QUERY, ip_params)

        self._save_local_store()
        logger.info(
            f"Successfully upserted persona '{profile.handle}' on '{profile.platform}' with post '{post.post_id}'."
        )

    def create_attribution_link(
        self,
        actor_id: str,
        persona_a_key: Dict[str, str],
        persona_b_key: Dict[str, str],
        confidence: float,
        reasons: List[str],
    ) -> None:
        """Create or merge ThreatActor root node and link two personas together.

        Creates:
        - (:ThreatActor {actor_id})
        - (:ThreatActor)-[:CONTROLS {confidence}]->(:Persona A)
        - (:ThreatActor)-[:CONTROLS {confidence}]->(:Persona B)
        - (:Persona A)-[:LINKED_TO {confidence, reasons, method: 'stylometry_v1'}]->(:Persona B)
        """
        handle_a = persona_a_key.get("handle") or persona_a_key.get("actor_handle", "")
        platform_a = (
            persona_a_key.get("platform")
            or persona_a_key.get("marketplace")
            or persona_a_key.get("forum_name", "")
        )
        handle_b = persona_b_key.get("handle") or persona_b_key.get("actor_handle", "")
        platform_b = (
            persona_b_key.get("platform")
            or persona_b_key.get("marketplace")
            or persona_b_key.get("forum_name", "")
        )
        timestamp_str = datetime.now(timezone.utc).isoformat()

        key_a = (handle_a, platform_a)
        key_b = (handle_b, platform_b)

        # 1. Update in-memory graph store
        if actor_id not in self._in_memory_store["threat_actors"]:
            self._in_memory_store["threat_actors"][actor_id] = {
                "actor_id": actor_id,
                "attribution_confidence": float(confidence),
                "first_seen": timestamp_str,
                "last_seen": timestamp_str,
            }
        else:
            actor = self._in_memory_store["threat_actors"][actor_id]
            actor["attribution_confidence"] = max(actor["attribution_confidence"], float(confidence))
            actor["last_seen"] = timestamp_str

        # Ensure personas exist in in-memory store
        for key in (key_a, key_b):
            if key not in self._in_memory_store["personas"]:
                self._in_memory_store["personas"][key] = {
                    "handle": key[0],
                    "platform": key[1],
                    "first_seen": timestamp_str,
                    "last_seen": timestamp_str,
                    "features": StylometricFeatures(),
                    "attribution_id": actor_id,
                }
            else:
                self._in_memory_store["personas"][key]["attribution_id"] = actor_id

        # CONTROLS edges
        if (actor_id, key_a) not in self._in_memory_store["controls"]:
            self._in_memory_store["controls"].append((actor_id, key_a))
        if (actor_id, key_b) not in self._in_memory_store["controls"]:
            self._in_memory_store["controls"].append((actor_id, key_b))

        # LINKED_TO edge
        link_edge = {
            "source": key_a,
            "target": key_b,
            "confidence": float(confidence),
            "reasons": list(reasons),
            "method": "stylometry_v1",
            "updated_at": timestamp_str,
        }
        # Update existing or append
        existing_idx = None
        for i, edge in enumerate(self._in_memory_store["linked_to"]):
            if edge["source"] == key_a and edge["target"] == key_b:
                existing_idx = i
                break
        if existing_idx is not None:
            self._in_memory_store["linked_to"][existing_idx] = link_edge
        else:
            self._in_memory_store["linked_to"].append(link_edge)

        # 2. Execute Cypher queries on live driver / mock driver
        if self._is_live_driver():
            params = {
                "actor_id": actor_id,
                "handle_a": handle_a,
                "platform_a": platform_a,
                "handle_b": handle_b,
                "platform_b": platform_b,
                "confidence": float(confidence),
                "reasons": list(reasons),
                "timestamp": timestamp_str,
            }
            self.driver.execute_write(CREATE_ATTRIBUTION_LINK_QUERY, params)

        self._save_local_store()
        logger.info(
            f"Created attribution link for ThreatActor '{actor_id}' between {key_a} and {key_b} (confidence={confidence:.2f})."
        )

    def link_persona_to_actor(
        self,
        actor_id: str,
        persona_key: Dict[str, str],
        confidence: float = 1.0,
    ) -> None:
        """Link a single persona to a ThreatActor cluster."""
        handle = persona_key.get("handle") or persona_key.get("actor_handle", "")
        platform = (
            persona_key.get("platform")
            or persona_key.get("marketplace")
            or persona_key.get("forum_name", "")
        )
        timestamp_str = datetime.now(timezone.utc).isoformat()
        key = (handle, platform)

        # In-memory store update
        if actor_id not in self._in_memory_store["threat_actors"]:
            self._in_memory_store["threat_actors"][actor_id] = {
                "actor_id": actor_id,
                "attribution_confidence": float(confidence),
                "first_seen": timestamp_str,
                "last_seen": timestamp_str,
            }
        if key not in self._in_memory_store["personas"]:
            self._in_memory_store["personas"][key] = {
                "handle": handle,
                "platform": platform,
                "first_seen": timestamp_str,
                "last_seen": timestamp_str,
                "features": StylometricFeatures(),
                "attribution_id": actor_id,
            }
        else:
            self._in_memory_store["personas"][key]["attribution_id"] = actor_id

        if (actor_id, key) not in self._in_memory_store["controls"]:
            self._in_memory_store["controls"].append((actor_id, key))

        if self._is_live_driver():
            params = {
                "actor_id": actor_id,
                "handle": handle,
                "platform": platform,
                "confidence": float(confidence),
                "timestamp": timestamp_str,
            }
            self.driver.execute_write(LINK_SINGLE_PERSONA_QUERY, params)

        self._save_local_store()

    def query_actor_network(self, actor_id: str) -> Dict[str, Any]:
        """Query and return the full threat actor network.

        Returns linked handles, marketplaces, shared wallets, IPs, PGP keys, posts,
        and attribution confidence.
        """
        # 1. Try querying Neo4j live driver / mock driver
        if self._is_live_driver():
            try:
                records = self.driver.execute_query(
                    QUERY_ACTOR_NETWORK_QUERY,
                    {"actor_id": actor_id},
                )
                if records and len(records) > 0:
                    row = records[0]
                    personas = [p for p in row.get("personas", []) if p and p.get("handle")]
                    marketplaces = [m for m in row.get("marketplaces", []) if m]
                    crypto_wallets = [
                        w for w in row.get("crypto_wallets", []) if w and w.get("address")
                    ]
                    pgp_keys = [k for k in row.get("pgp_keys", []) if k]
                    ip_addresses = [i for i in row.get("ip_addresses", []) if i]
                    posts = [post for post in row.get("posts", []) if post and post.get("post_id")]
                    linkages = [
                        l
                        for l in row.get("linkages", [])
                        if l and l.get("target_handle") and l.get("confidence") is not None
                    ]

                    # If actor exists in DB
                    conf = float(row.get("attribution_confidence", 0.0) or 0.0)
                    if linkages:
                        avg_conf = sum(l["confidence"] for l in linkages) / len(linkages)
                    else:
                        avg_conf = conf

                    return {
                        "actor_id": actor_id,
                        "attribution_confidence": round(avg_conf, 4),
                        "handles": personas,
                        "marketplaces": marketplaces,
                        "crypto_wallets": crypto_wallets,
                        "pgp_keys": pgp_keys,
                        "ip_addresses": ip_addresses,
                        "posts": posts,
                        "linkages": linkages,
                        "total_posts": len(posts),
                        "total_wallets": len(crypto_wallets),
                    }
            except Exception as exc:
                logger.warning(f"Error querying live Neo4j for actor '{actor_id}': {exc}")

        # 2. Fallback to in-memory graph store
        actor = self._in_memory_store["threat_actors"].get(actor_id)
        if not actor:
            return {
                "actor_id": actor_id,
                "attribution_confidence": 0.0,
                "handles": [],
                "marketplaces": [],
                "crypto_wallets": [],
                "pgp_keys": [],
                "ip_addresses": [],
                "posts": [],
                "linkages": [],
                "total_posts": 0,
                "total_wallets": 0,
            }

        # Find controlled personas
        controlled_keys = [
            key for (aid, key) in self._in_memory_store["controls"] if aid == actor_id
        ]
        personas_list = []
        marketplaces_set = set()
        for key in controlled_keys:
            p_data = self._in_memory_store["personas"].get(key, {})
            personas_list.append(
                {
                    "handle": p_data.get("handle", key[0]),
                    "platform": p_data.get("platform", key[1]),
                    "first_seen": p_data.get("first_seen", ""),
                    "last_seen": p_data.get("last_seen", ""),
                }
            )
            marketplaces_set.add(key[1])

        # Find posts
        posts_list = []
        for key in controlled_keys:
            for (p_key, post_id) in self._in_memory_store["authored"]:
                if p_key == key:
                    post_data = self._in_memory_store["posts"].get(post_id, {})
                    posts_list.append(
                        {
                            "post_id": post_id,
                            "timestamp": post_data.get("timestamp", ""),
                            "handle": key[0],
                            "platform": key[1],
                        }
                    )

        # Find wallets
        wallets_list = []
        seen_wallets = set()
        for key in controlled_keys:
            for (p_key, address) in self._in_memory_store["utilizes_wallet"]:
                if p_key == key and address not in seen_wallets:
                    seen_wallets.add(address)
                    w_data = self._in_memory_store["wallets"].get(address, {})
                    wallets_list.append(
                        {
                            "address": address,
                            "currency": w_data.get("currency", "UNKNOWN"),
                        }
                    )

        # Find PGP keys
        pgp_list = []
        seen_pgp = set()
        for key in controlled_keys:
            for (p_key, fp) in self._in_memory_store["owns_key"]:
                if p_key == key and fp not in seen_pgp:
                    seen_pgp.add(fp)
                    pgp_list.append(fp)

        # Find IPs
        ips_list = []
        seen_ips = set()
        for key in controlled_keys:
            for (p_key, ip) in self._in_memory_store["observed_ip"]:
                if p_key == key and ip not in seen_ips:
                    seen_ips.add(ip)
                    ips_list.append(ip)

        # Find linkages
        linkages_list = []
        for link in self._in_memory_store["linked_to"]:
            if link["source"] in controlled_keys or link["target"] in controlled_keys:
                linkages_list.append(
                    {
                        "source_handle": link["source"][0],
                        "source_platform": link["source"][1],
                        "target_handle": link["target"][0],
                        "target_platform": link["target"][1],
                        "confidence": link["confidence"],
                        "reasons": link["reasons"],
                        "method": link["method"],
                    }
                )

        if linkages_list:
            avg_conf = sum(l["confidence"] for l in linkages_list) / len(linkages_list)
        else:
            avg_conf = actor.get("attribution_confidence", 0.0)

        return {
            "actor_id": actor_id,
            "attribution_confidence": round(avg_conf, 4),
            "handles": personas_list,
            "marketplaces": sorted(list(marketplaces_set)),
            "crypto_wallets": wallets_list,
            "pgp_keys": pgp_list,
            "ip_addresses": ips_list,
            "posts": posts_list,
            "linkages": linkages_list,
            "total_posts": len(posts_list),
            "total_wallets": len(wallets_list),
        }

    def get_candidate_profiles(self) -> List[ThreatActorProfile]:
        """Retrieve existing persona profiles from graph for entity resolution matching."""
        if self._is_live_driver():
            try:
                records = self.driver.execute_query(GET_ALL_PROFILES_QUERY)
                profiles = []
                for row in records:
                    wallets = [
                        CryptoWallet(currency=w.get("currency", "BTC"), address=w.get("address", ""))
                        for w in row.get("crypto_wallets", [])
                        if w and w.get("address")
                    ]
                    pgp_keys = [k for k in row.get("pgp_keys", []) if k]
                    ip_addresses = [i for i in row.get("ip_addresses", []) if i]
                    features = StylometricFeatures(
                        average_sentence_length=row.get("avg_sentence_length", 0.0) or 0.0,
                        average_word_length=row.get("avg_word_length", 0.0) or 0.0,
                        type_token_ratio=row.get("type_token_ratio", 0.0) or 0.0,
                        hapax_legomena_ratio=row.get("hapax_ratio", 0.0) or 0.0,
                        paragraph_count=row.get("paragraph_count", 1) or 1,
                        uppercase_ratio=row.get("uppercase_ratio", 0.0) or 0.0,
                        character_count=row.get("character_count", 0) or 0,
                    )
                    profiles.append(
                        ThreatActorProfile(
                            handle=row["handle"],
                            platform=row["platform"],
                            features=features,
                            identifiers=ExtractedIdentifiers(
                                crypto_wallets=wallets,
                                pgp_keys=pgp_keys,
                                ip_addresses=ip_addresses,
                            ),
                            attribution_id=row.get("attribution_id"),
                        )
                    )
                if profiles:
                    return profiles
            except Exception as exc:
                logger.warning(f"Error fetching profiles from live DB: {exc}")

        # Fallback to in-memory store
        profiles = []
        for key, p_data in self._in_memory_store["personas"].items():
            # Get wallets
            wallets = []
            for (p_key, address) in self._in_memory_store["utilizes_wallet"]:
                if p_key == key:
                    w_data = self._in_memory_store["wallets"].get(address, {})
                    wallets.append(
                        CryptoWallet(
                            currency=w_data.get("currency", "UNKNOWN"),
                            address=address,
                        )
                    )
            # PGP
            pgp_keys = [
                fp
                for (p_key, fp) in self._in_memory_store["owns_key"]
                if p_key == key
            ]
            # IPs
            ip_addresses = [
                ip
                for (p_key, ip) in self._in_memory_store["observed_ip"]
                if p_key == key
            ]

            features = p_data.get("features", StylometricFeatures())
            if isinstance(features, dict):
                features = StylometricFeatures(**features)

            profiles.append(
                ThreatActorProfile(
                    handle=p_data.get("handle", key[0]),
                    platform=p_data.get("platform", key[1]),
                    features=features,
                    identifiers=ExtractedIdentifiers(
                        crypto_wallets=wallets,
                        pgp_keys=pgp_keys,
                        ip_addresses=ip_addresses,
                    ),
                    attribution_id=p_data.get("attribution_id"),
                )
            )
        return profiles

    def clear(self) -> None:
        """Reset in-memory storage (and execute Cypher detach delete if live)."""
        self._in_memory_store = {
            "threat_actors": {},
            "personas": {},
            "posts": {},
            "wallets": {},
            "pgp_keys": {},
            "ips": {},
            "controls": [],
            "authored": [],
            "utilizes_wallet": [],
            "owns_key": [],
            "observed_ip": [],
            "linked_to": [],
        }
        if self.store_path and Path(self.store_path).exists():
            try:
                Path(self.store_path).unlink()
            except Exception:
                pass
        if self._is_live_driver():
            try:
                self.driver.execute_write("MATCH (n) DETACH DELETE n")
            except Exception as exc:
                logger.warning(f"Could not clear Neo4j database: {exc}")
