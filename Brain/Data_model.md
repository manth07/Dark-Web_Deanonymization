# Data Model — Neo4j Graph Schema

Owned by: `/ai-graph`. Any change here must be reflected in `API_Contracts.md`
and mentioned in `Changelog.md` — this is the contract `backend` reads
against.

## 1. Node Labels

| Label | Key property | Other properties |
|---|---|---|
| `ThreatActor` | `actor_id` (generated on merge) | `attribution_confidence`, `category`, `last_scan_date`, `first_seen`, `last_seen` |
| `Handle` | `handle_name` + `marketplace` (composite unique) | `source`, `first_seen`, `last_seen` |
| `Marketplace` | `name` | `type` (marketplace/forum/deep-web), `reliability_score` |
| `Post` | `post_id` | `raw_text_ref`, `timestamp`, `source` |
| `PGPKey` | `fingerprint` | `key_block_ref`, `first_seen` |
| `Wallet` | `address` | `chain` (BTC/ETH/XMR/...), `first_seen` |
| `HiddenService` | `onion_hash` (hashed, never store raw .onion in plaintext logs) | `descriptor_seen_at` |
| `InfraIndicator` | `indicator_id` | `type` (ssl_cert / banner / status_page / descriptor_pattern), `value_hash`, `detected_at` |
| `ClearnetHost` | `host` | `resolved_via`, `confidence` |
| `PersonaCluster` | `cluster_id` | `centroid_ref`, `created_at`, `method` |

## 2. Relationship Types

| Relationship | From → To | Key properties |
|---|---|---|
| `USES_HANDLE` | `ThreatActor → Handle` | `confidence`, `source` |
| `POSTED_ON` | `Handle → Marketplace` | `timestamp` |
| `AUTHORED` | `Handle → Post` | — |
| `HAS_PGP_KEY` | `ThreatActor → PGPKey` | `confidence` |
| `OWNS_WALLET` | `ThreatActor → Wallet` | `confidence`, `evidence_source` |
| `HOSTED_AT` | `Marketplace → HiddenService` | — |
| `EXHIBITS` | `HiddenService → InfraIndicator` | `detected_at` |
| `RESOLVES_TO` | `InfraIndicator → ClearnetHost` | `confidence`, `method` |
| `SIMILAR_STYLE_TO` | `Handle → Handle` | `cosine_similarity` (float), `computed_at`, `model` |
| `SAME_PERSONA_AS` | `ThreatActor → ThreatActor` | `confidence`, `evidence` (list of contributing signal types) |
| `MEMBER_OF` | `Handle → PersonaCluster` | `distance_to_centroid` |
| `VOUCHES_FOR` | `Handle → Handle` | `trust_weight`, `source` |

## 3. Attribution Confidence Model

Each signal type contributes a weighted vote toward `attribution_confidence`
on the eventual merged `ThreatActor` node:

| Signal | Typical weight | Rationale |
|---|---|---|
| Shared PGP fingerprint | very high | Cryptographically hard to fake accidentally |
| Shared wallet address (reused, not mixed) | high | Strong but can be shared services |
| Infra correlation (`RESOLVES_TO`) | high | Direct technical leak |
| `SIMILAR_STYLE_TO` above threshold | medium | Behavioural, not identity-proof alone |
| Marketplace trust-link overlap | low–medium | Social signal, easy to fabricate |

`attribution_confidence` is a normalized aggregate (0–1) of contributing edge
weights — store the contributing evidence list on `SAME_PERSONA_AS` so the
dashboard can explain *why* two actors were merged (required for
auditability, PRD §7).

## 4. Cypher — Schema Setup

```cypher
CREATE CONSTRAINT actor_id IF NOT EXISTS FOR (a:ThreatActor) REQUIRE a.actor_id IS UNIQUE;
CREATE CONSTRAINT handle_unique IF NOT EXISTS FOR (h:Handle) REQUIRE (h.handle_name, h.marketplace) IS NODE KEY;
CREATE CONSTRAINT pgp_fp IF NOT EXISTS FOR (k:PGPKey) REQUIRE k.fingerprint IS UNIQUE;
CREATE CONSTRAINT wallet_addr IF NOT EXISTS FOR (w:Wallet) REQUIRE w.address IS UNIQUE;
CREATE INDEX actor_confidence IF NOT EXISTS FOR (a:ThreatActor) ON (a.attribution_confidence);
CREATE INDEX post_timestamp IF NOT EXISTS FOR (p:Post) ON (p.timestamp);
```

## 5. Cypher — Common Operations

**Upsert a handle and link to actor (idempotent, always `MERGE`):**
```cypher
MERGE (a:ThreatActor {actor_id: $actor_id})
  ON CREATE SET a.attribution_confidence = 0.0, a.category = $category,
                a.first_seen = $ts, a.last_seen = $ts
  ON MATCH SET a.last_seen = $ts
MERGE (h:Handle {handle_name: $handle, marketplace: $marketplace})
  ON CREATE SET h.source = $source, h.first_seen = $ts
MERGE (a)-[r:USES_HANDLE]->(h)
  ON CREATE SET r.confidence = $confidence, r.source = $source;
```

**Write a stylometric similarity edge:**
```cypher
MATCH (h1:Handle {handle_name: $h1, marketplace: $m1})
MATCH (h2:Handle {handle_name: $h2, marketplace: $m2})
MERGE (h1)-[s:SIMILAR_STYLE_TO]-(h2)
  SET s.cosine_similarity = $score, s.computed_at = $ts, s.model = $model;
```

**Query: actors above a confidence threshold within a timeline:**
```cypher
MATCH (a:ThreatActor)
WHERE a.attribution_confidence >= $min_conf
  AND a.last_seen >= $start AND a.first_seen <= $end
RETURN a ORDER BY a.attribution_confidence DESC;
```

## 6. Raw Text Storage

Raw scraped text is **not** stored as a node property (keeps the graph light).
Store it in the raw-store (filesystem/Mongo, per `Scraping_spec.md`) and keep
only a `raw_text_ref` pointer on `Post`. Only derived features (n-grams,
punctuation frequency vectors, embeddings) live in `ai-graph`'s working
storage, not in Neo4j itself, unless a summarized feature vector is needed for
UI display.
