# PRD — Dark Web Threat Actor De-anonymization

**SIH ID:** 26151 | **Org:** NTRO | **Category:** Software

## 1. Problem (condensed)

Threat actors hide behind Tor hidden services to run drug/arms sales, stolen
data/hacking services, money laundering, and terror financing. Attribution is
the core bottleneck. Build a system that continuously gathers footprints from
marketplaces/forums/deep web, links them to identifying information, and
surfaces likely real-world origins with a confidence score — queryable through
a dashboard.

## 2. Goals

- G1: Detect Tor hidden-service misconfigurations and correlate them to
  clearnet infrastructure.
- G2: Build a cross-marketplace relationship graph of handles, PGP keys,
  wallets, and trust links.
- G3: Use stylometric + behavioural AI analysis to link rebranded/migrated
  personas to known actors.
- G4: Provide a queryable dashboard (timeline-filterable) with CSV/JSON/report
  export.
- G5: Run autonomously against sources of acceptable quality/reliability.

## 3. Non-Goals (hackathon prototype scope)

- Live interaction with marketplaces (purchases, messaging).
- Automated legal/takedown action.
- Real-time nation-scale crawling (a representative sample pipeline is enough
  to demonstrate the method).

## 4. Users

- **Analyst** — runs queries, reviews actor profiles and confidence scores,
  exports evidence.
- **Investigator/Admin** — manages sources, reviews scan health, configures
  autonomous mode.

## 5. Features → Capability Mapping

| Feature | Capability | Owning folder |
|---|---|---|
| Infra fingerprint matching (SSL, banners, status pages → clearnet host) | 1 | scraper + ai-graph |
| Cross-marketplace identity graph (handles, PGP, wallets, trust) | 2 | ai-graph (Neo4j) |
| Stylometric persona linking (rebrand/migration detection) | 3 | ai-graph |
| Dashboard: query by actor/timeline/category/confidence | GUI | frontend + backend |
| Export CSV / JSON / report | Delivery | backend |
| Autonomous scan scheduling | Ops | scraper + backend |

## 6. Functional Requirements

- FR1: System stores actor profiles with identifiers, category, attribution
  confidence, last scan date, and source.
- FR2: System computes a stylometric similarity score between any two text
  samples and exposes it as a graph edge with weight.
- FR3: System merges (not duplicates) actor nodes across sources using
  identifier + similarity matching.
- FR4: System allows querying by timeline window.
- FR5: System exports the active result set in CSV, JSON, and a human-readable
  report format.

## 7. Non-Functional Requirements

- Reproducible locally via Docker (no cloud dependency for the core AI/graph
  stack).
- Every attribution claim traceable back to source + evidence (auditability).
- Confidence scores must be explainable (which signals contributed).
- Graceful degradation if a source or a model is temporarily unreachable.

## 8. Success Metrics (demo)

- Correctly re-links ≥ 90% of synthetic "rebranded persona" pairs in the test
  set at the chosen similarity threshold.
- Zero silent data loss on ingestion errors (all failures logged/queued).
- Dashboard query returns in < 2s against the demo graph.

## 9. Deliverables

- Working end-to-end pipeline (scraper → ai-graph → Neo4j → backend → frontend).
- Sample dataset + reproducible demo script.
- Export in CSV, JSON, report formats.
