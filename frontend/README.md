# Frontend Service — Dark Web Threat Actor De-anonymization

**Technology Stack:** Next.js, React Flow, Tailwind CSS, TypeScript

## Overview
The `frontend` service delivers an interactive investigative dashboard designed for cyber intelligence analysts, NTRO operators, and law enforcement.

## Key Features
- **Actor Network Topology (React Flow)**: Visualizes threat actor clusters, connected dark web aliases, cross-marketplace presence, shared cryptocurrency wallets, and PGP keys as an interactive graph.
- **Attribution & Timeline Explorer**: Filter actors and activities by date range, marketplace, and attribution confidence score ($\ge 0.80$).
- **Evidence & Audit Trail Inspector**: Deep dive into stylometric metric breakdowns, function word alignments, and cryptographic linkage reasons.
- **Intelligence Export**: Trigger one-click exports for NTRO JSON deliverables, analyst CSV spreadsheets, and printable executive briefings.

## Architecture
- Consumes backend REST API endpoints (`/actors`, `/actors/{id}`, `/actors/{id}/graph`, `/export`).
- Real-time updates for streaming intelligence alerts.
