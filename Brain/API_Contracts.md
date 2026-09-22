# API Contracts

Purpose: the four folders develop in isolation (`Master_rules.md`). This is
the file that keeps that isolation from turning into an integration disaster
on demo day — it's the single place all cross-folder interfaces are defined.
**Any change to a contract below must be made in the same PR as the code
change, plus a `Changelog.md` entry.**

## 1. `scraper` → `ai-graph`

Full schema: `Scraping_spec.md` §2. Summary: JSON records with
`source_type`, `source_id`, `marketplace`, `actor_handle`, `raw_text`,
`page_metadata`, `timestamp`, `reliability_score`, landing in the shared
raw-store.

**Versioning:** if a field is added, it must be optional with a sensible
default so `ai-graph`'s consumer doesn't break on old records. Breaking
changes require a version bump in the record (`schema_version` field) and a
note in `Changelog.md`.

## 2. `ai-graph` → `backend`

**Contract = the Neo4j schema itself** (`Data_model.md`). `backend` connects
directly to Neo4j as a read-only consumer of the graph `ai-graph` writes.

Rules:
- `backend` never writes `ThreatActor`/`Handle`/identity nodes — it may only
  write its own operational nodes/properties if needed (e.g. `query_log`),
  clearly namespaced to avoid collision.
- Any new node label, relationship type, or property `ai-graph` needs for the
  dashboard to display must be added to `Data_model.md` first, then
  implemented — `backend` should never have to reverse-engineer the schema
  from a live query.
- Suggested read-query examples for `backend` to build endpoints around live
  in `Data_model.md` §5 — extend that list rather than inventing ad hoc
  queries undocumented anywhere.

## 3. `backend` → `frontend`

REST API (owned/defined by `backend`). Minimum expected endpoints for this
project:

| Endpoint | Purpose |
|---|---|
| `GET /actors?min_confidence=&start=&end=&category=` | timeline/confidence-filtered actor list |
| `GET /actors/{actor_id}` | full profile: identifiers, evidence, linked personas |
| `GET /actors/{actor_id}/graph` | relationship subgraph for visualization |
| `GET /export?format=csv|json|report&...filters` | export current result set |

(`backend` teammate owns the exact shape/versioning of this API; this table
is the minimum the frontend needs to build against — extend, don't shrink.)

## 4. Change Process

1. Propose the contract change in the relevant section above (PR against
   `docs/`).
2. Tag the owner of the *other* affected folder for review.
3. Merge docs change + implementation together.
4. Add a `Changelog.md` entry noting which folders are affected.
