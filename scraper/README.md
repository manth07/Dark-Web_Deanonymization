# Scraper Service — Tor & Dark Web Crawler / Intelligence Collection

**Technology Stack:** Python 3.11, Tor SOCKS5 Proxy, Playwright / Scrapy, BeautifulSoup4

## Overview
The `scraper` service autonomously navigates Tor hidden services (`.onion` sites) across dark web forums, pastebins, and marketplaces to collect intelligence footprints.

## Key Capabilities
- **Tor Proxy Isolation**: All outbound requests strictly routed through dedicated Tor daemon proxies with circuit rotation.
- **Scraping Specification Conformance**: Emits structured JSON records strictly conforming to `Brain/Scraping_spec.md` (`record_id`, `source_type`, `marketplace`, `actor_handle`, `raw_text`, `timestamp`, `reliability_score`).
- **Infrastructure Fingerprinting**: Captures server response headers, TLS/SSL certificates, Favicon hashes (MurmurHash3), and clearnet leak indicators.
- **Data Ingestion Hand-off**: Drops raw records into `data/incoming/` for consumption by the `ai-graph` ingestion pipeline.
