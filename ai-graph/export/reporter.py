"""Intelligence Reporter for exporting structured NTRO deliverables (JSON, CSV, and text summaries)."""
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import get_logger
from graph.repository import ThreatGraphRepository

logger = get_logger("export.reporter")


class IntelligenceReporter:
    """Generates analytical threat intelligence reports from the graph intelligence repository."""

    def __init__(self, repository: Optional[ThreatGraphRepository] = None) -> None:
        self.repository = repository or ThreatGraphRepository()

    def generate_summary_report(self, actor_id: str) -> str:
        """Generate a human-readable textual intelligence briefing summarizing the threat actor."""
        network = self.repository.query_actor_network(actor_id)
        if not network or not network.get("handles"):
            return f"Threat Actor [{actor_id}] has no observed network activity or associated personas."

        handles = [h["handle"] for h in network.get("handles", [])]
        unique_handles = sorted(list(set(handles)))
        platforms = network.get("marketplaces", [])
        confidence = network.get("attribution_confidence", 0.0)
        wallets = network.get("crypto_wallets", [])
        pgp_keys = network.get("pgp_keys", [])
        ips = network.get("ip_addresses", [])
        posts = network.get("posts", [])
        linkages = network.get("linkages", [])

        # Format handles
        if len(unique_handles) == 1:
            handles_str = f"'{unique_handles[0]}'"
        elif len(unique_handles) == 2:
            handles_str = f"'{unique_handles[0]}' and '{unique_handles[1]}'"
        else:
            handles_str = ", ".join(f"'{h}'" for h in unique_handles[:-1]) + f", and '{unique_handles[-1]}'"

        # Collect evidence reasons
        all_reasons = []
        for link in linkages:
            all_reasons.extend(link.get("reasons", []))
        unique_reasons = sorted(list(set(all_reasons)))

        evidence_str = (
            "; ".join(unique_reasons)
            if unique_reasons
            else f"Automated entity resolution (confidence: {confidence:.2f})"
        )

        wallets_summary = (
            ", ".join(f"{w.get('currency', 'CRYPTO')}:{w.get('address', '')}" for w in wallets)
            if wallets
            else "None observed"
        )
        pgp_summary = (
            ", ".join(k[:20] + "..." if len(k) > 20 else k for k in pgp_keys)
            if pgp_keys
            else "None observed"
        )
        ips_summary = ", ".join(ips) if ips else "None observed"

        briefing = (
            f"[NTRO THREAT INTELLIGENCE BRIEFING]\n"
            f"Threat Actor [{actor_id}] operates across {len(platforms)} marketplace(s) "
            f"({', '.join(platforms)}) under handles {handles_str}.\n"
            f"Attribution Confidence: {confidence:.2f}\n"
            f"Linkage Evidence: {evidence_str}\n"
            f"Harvested Cryptographic & Infrastructure Indicators:\n"
            f"  - Wallets: {wallets_summary}\n"
            f"  - PGP Keys: {pgp_summary}\n"
            f"  - IP Addresses: {ips_summary}\n"
            f"Total Observed Forum Posts: {len(posts)}"
        )
        return briefing

    def export_json(self, actor_id: str, output_path: str) -> Dict[str, Any]:
        """Export deep threat actor profile conforming to NTRO intelligence deliverable format."""
        network = self.repository.query_actor_network(actor_id)

        # Timeline sorted chronologically
        timeline = sorted(
            network.get("posts", []),
            key=lambda p: p.get("timestamp", ""),
        )

        deliverable = {
            "root_actor_id": network.get("actor_id", actor_id),
            "actor_id": network.get("actor_id", actor_id),
            "attribution_confidence": network.get("attribution_confidence", 0.0),
            "confidence_score": network.get("attribution_confidence", 0.0),
            "alias_handles": [h["handle"] for h in network.get("handles", [])],
            "platforms": network.get("marketplaces", []),
            "linked_personas": network.get("handles", []),
            "crypto_wallets": network.get("crypto_wallets", []),
            "wallets": network.get("crypto_wallets", []),
            "pgp_fingerprints": network.get("pgp_keys", []),
            "pgp_keys": network.get("pgp_keys", []),
            "ip_addresses": network.get("ip_addresses", []),
            "timestamp_timeline": timeline,
            "linkages": network.get("linkages", []),
            "summary_briefing": self.generate_summary_report(actor_id),
            "metadata": {
                "generated_by": "NTRO Dark Web Deanonymization Engine v1.0",
                "classification": "CONFIDENTIAL // LAW ENFORCEMENT SENSITIVE",
            },
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(deliverable, f, indent=2)

        logger.info(f"Exported NTRO JSON threat deliverable for '{actor_id}' to '{output_path}'.")
        return deliverable

    def export_csv(self, actor_id: str, output_path: str) -> None:
        """Flatten persona-to-identifier mappings for analyst spreadsheet ingestion."""
        network = self.repository.query_actor_network(actor_id)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "actor_id",
            "handle",
            "platform",
            "identifier_type",
            "identifier_value",
            "attribution_confidence",
        ]

        rows = []
        conf = network.get("attribution_confidence", 0.0)
        handles = network.get("handles", [])

        # Default persona reference if no handles
        if not handles:
            rows.append({
                "actor_id": actor_id,
                "handle": "UNKNOWN",
                "platform": "UNKNOWN",
                "identifier_type": "none",
                "identifier_value": "none",
                "attribution_confidence": conf,
            })
        else:
            for p in handles:
                handle = p.get("handle", "")
                platform = p.get("platform", "")

                has_identifiers = False

                # Crypto Wallets
                for wallet in network.get("crypto_wallets", []):
                    has_identifiers = True
                    rows.append({
                        "actor_id": actor_id,
                        "handle": handle,
                        "platform": platform,
                        "identifier_type": f"crypto_wallet_{wallet.get('currency', 'UNKNOWN')}",
                        "identifier_value": wallet.get("address", ""),
                        "attribution_confidence": conf,
                    })

                # PGP Keys
                for pgp in network.get("pgp_keys", []):
                    has_identifiers = True
                    rows.append({
                        "actor_id": actor_id,
                        "handle": handle,
                        "platform": platform,
                        "identifier_type": "pgp_key",
                        "identifier_value": pgp,
                        "attribution_confidence": conf,
                    })

                # IP Addresses
                for ip in network.get("ip_addresses", []):
                    has_identifiers = True
                    rows.append({
                        "actor_id": actor_id,
                        "handle": handle,
                        "platform": platform,
                        "identifier_type": "ip_address",
                        "identifier_value": ip,
                        "attribution_confidence": conf,
                    })

                if not has_identifiers:
                    rows.append({
                        "actor_id": actor_id,
                        "handle": handle,
                        "platform": platform,
                        "identifier_type": "persona_only",
                        "identifier_value": "no_hard_identifiers",
                        "attribution_confidence": conf,
                    })

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Exported NTRO CSV analyst spreadsheet for '{actor_id}' to '{output_path}'.")
