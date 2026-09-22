# Data Sources

## 1. Source Categories

| Category | Examples of signal | Notes |
|---|---|---|
| Dark web marketplaces (Tor hidden services) | listings, seller profiles, PGP blocks, review/trust text | primary source for identifiers |
| Dark web forums | discussion posts, handle history, migration announcements | primary source for stylometry |
| Deep web (non-indexed but not Tor) | leak/paste sites, breach forums mirrored on clearnet | secondary corroboration |
| Hidden service infrastructure | HTTP headers, TLS certs, default banners, `server-status`/status pages, descriptor timing | feeds infra-correlation (capability 1) |

*(No real `.onion` addresses or live source URLs are stored in this
repo's docs — see `Security.md`. Source registries live in the scraper's
config, access-controlled.)*

## 2. Per-Record Fields Expected From Any Source

- `source_type` (marketplace / forum / deep-web / infra-scan)
- `source_id` (hashed/opaque reference, not the raw address)
- `actor_handle`
- `raw_text` (for text sources) or `page_metadata` (for infra sources)
- `timestamp`
- `reliability_score` (see below)

## 3. Reliability Scoring (rubric)

| Tier | Description | Score |
|---|---|---|
| A | Long-running marketplace with consistent identifier history, cross-corroborated | 0.8–1.0 |
| B | Established forum, some corroboration | 0.5–0.8 |
| C | New/unverified source, single mention | 0.2–0.5 |
| D | Anonymous leak with no corroboration | < 0.2 |

`reliability_score` feeds into `attribution_confidence` alongside the signal
weights in `Data_model.md` §3.

## 4. Legal & Ethical Constraints

- **Authorized use only.** This system is designed for NTRO's lawful
  investigative mandate. It is passive OSINT collection — no purchases, no
  direct interaction with threat actors, no active exploitation of
  misconfigurations beyond passive observation.
- **Development and testing never touch live dark web sources.** Use the
  synthetic/sample corpus described below.
- Any live-source integration is an operational decision outside the scope of
  this hackathon prototype.

## 5. Development Dataset

- Location: `/ai-graph/data/sample_texts.json` (and mirrored raw-record
  fixtures for `scraper`/`backend` integration testing).
- Content: synthetic forum/marketplace posts, written to include a handful of
  "known" persona pairs with deliberately similar style but different handles
  — this is what `Testing.md`'s entity-resolution tests validate against.
- No real personal data, no real identifiers, no real `.onion` addresses.
