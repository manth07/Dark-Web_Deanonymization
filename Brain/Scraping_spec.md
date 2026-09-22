# Scraping Spec

Owned by: `/scraper`. Documented here because `/ai-graph` consumes its
output directly — this file is the **contract**, not an implementation guide
for the scraper module itself.

## 1. Responsibilities (high-level, owned by scraper teammate)

- Passive collection from configured marketplaces/forums/deep-web sources
  through a Tor proxy (isolated container, see `Docker.md` / `Security.md`).
- Infra fingerprinting: capture HTTP headers, TLS certificate details, banner
  text, and any exposed status pages for each hidden service touched.
- Rate limiting + circuit rotation (OPSEC for the scraper itself — out of
  scope for `ai-graph`).
- Write output as records matching the schema below to the shared raw-store.

## 2. Output Contract → `ai-graph`

Every scraped unit becomes one JSON record:

```json
{
  "record_id": "uuid",
  "source_type": "marketplace | forum | deep-web | infra-scan",
  "source_id": "opaque-hash",
  "marketplace": "string",
  "actor_handle": "string",
  "raw_text": "string (for text sources)",
  "page_metadata": {
    "http_headers": {},
    "tls_cert_fingerprint": "string|null",
    "banner_text": "string|null",
    "status_page_exposed": "bool"
  },
  "timestamp": "ISO-8601",
  "reliability_score": 0.0
}
```

- `raw_text` is required for anything `ai-graph` will run stylometry on;
  `page_metadata` is required for anything feeding infra correlation.
- Records land in the shared raw-store (filesystem drop folder or
  Mongo/Postgres collection — see `TRD.md` §5); `ai-graph` polls/consumes from
  there, never calls the scraper directly.

## 3. Minimum Text Requirements for Stylometry

`ai-graph`'s feature extraction needs a minimum token count to produce a
meaningful stylometric profile (see `Error_Handling.md` for the reject path).
Recommend scraper tags very short records (`< 50 tokens`) so `ai-graph` can
skip them without a wasted embedding call.

## 4. Independence From the Live Scraper

`ai-graph` must be fully buildable and testable against
`data/sample_texts.json` fixtures matching this exact schema, with zero
dependency on the scraper being online. Integration with real scraper output
happens only in `Phases.md` Phase 6.
