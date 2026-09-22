"""Synthetic Dark Web Corpus Generator for offline development and testing.

Produces realistic threat actor posts across simulated dark web forums with planted
stylometric archetypes, cryptocurrency wallets, PGP fingerprints, and IP leakage.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from schemas.raw_post import RawForumPost

# Standard PGP key block fixture for Persona A & C
SAMPLE_PGP_BLOCK = (
    "-----BEGIN PGP PUBLIC KEY BLOCK-----\n"
    "mQENBF2v6wEBCADL+SAMPLE+THREAT+INTEL+KEY+BLOCK+DATA+FOR+STYLOMETRY+\n"
    "TESTING+PURPOSES+ONLY+4A5B6C7D8E9F0A1B2C3D4E5F6A7B8C9D0E1F2A3B==\n"
    "-----END PGP PUBLIC KEY BLOCK-----"
)
SAMPLE_PGP_FINGERPRINT = "4A5B6C7D8E9F0A1B2C3D4E5F6A7B8C9D0E1F2A3B"

PERSONA_TEMPLATES = {
    "ShadowBroker": {
        "forum": "DreadClone",
        "posts": [
            (
                "NEW CORPORATE LEAK... 50K EMPLOYEE RECORDS... DIRECT ACCESS TO SQL REPO... "
                "NO TIME WASTERS. ESCROW ONLY... BTC PAYMENT REQUIRED. "
                "WALLET: bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s... PGP KEY BELOW:\n"
                f"{SAMPLE_PGP_BLOCK}"
            ),
            (
                "CREDENTIALS VERIFIED... EXPLOIT CHAIN READY FOR APACHE... "
                "FAST TRANSACTIONS ONLY... URGENT INQUIRIES VIA PGP... "
                "PRICE: 0.5 BTC. WALLET: bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s... "
                "FINGERPRINT: " + SAMPLE_PGP_FINGERPRINT
            ),
            (
                "DATABASE DUMP PART 2... MEDICAL PROVIDER NETWORK... "
                "RAW DUMP WITH SSN AND PASSWORDS... ESCROW ONLY... "
                "CONTACT PGP... NO CHAT ON CLEARNET... BTC ONLY..."
            ),
            (
                "SYSTEM ACCESS SOLD... REMAINING LOGS DISCOUNTED... "
                "LIMITED TIME OFFER... SEND TRANSACTION ID TO ESCROW... "
                "BTC ADDRESS: bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s..."
            ),
            (
                "ZERO-DAY POC TESTED... ROOT PRIVILEGES CONFIRMED... "
                "SERIOUS BUYERS ONLY... PRICE IS NON-NEGOTIABLE... "
                "COMMUNICATIONS ENCRYPTED VIA PGP... ESCROW MANDATORY..."
            ),
            (
                "FINAL BATCH OF TOKENS... API KEYS FOR AWS CLOUD... "
                "CONFIRMED WORKING TODAY... FAST DEAL... BTC PAYMENTS ONLY... "
                "REPLY WITH YOUR PGP PUBLIC KEY..."
            ),
        ],
        "titles": [
            "Corporate SQL Leak [Verified]",
            "Apache Zero-Day Exploit Ready",
            "Medical Network Full Dump",
            "Discounted Access Logs",
            "Kernel PrivEsc Proof of Concept",
            "AWS Production Cloud Tokens",
        ],
    },
    "CryptoRebel": {
        "forum": "BreachNode",
        "posts": [
            (
                "The epistemological hegemony of state-sanctioned surveillance mechanisms inevitably "
                "demands a rigorous paradigm shift toward zero-knowledge mathematical primitives; "
                "furthermore, legacy transparency protocols fail catastrophically under adversarial graph analysis. "
                "For confidential correspondence, deposit bounty to Monero ring address: "
                "44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otKEfZagUopA9996oReoStZ6CHngAoRMa25VrWAFGLvmjh2QW51Uv; "
                "we reject clearnet compromise in perpetuity."
            ),
            (
                "A systematic deconstruction of modern biometric authentication infrastructures reveals profound "
                "architectural vulnerabilities; consequently, sovereign actors must deploy decentralized mixnets "
                "to preserve operational deniability. Contributions supporting our reverse-engineering whitepaper "
                "may be remitted exclusively via XMR: "
                "44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otKEfZagUopA9996oReoStZ6CHngAoRMa25VrWAFGLvmjh2QW51Uv; "
                "further academic dissections shall follow forthwith."
            ),
            (
                "Our theoretical discourse regarding quantum-resistant lattice cryptography suggests that contemporary "
                "elliptic-curve signatures are inherently ephemeral; moreover, side-channel timing analysis demonstrates "
                "conclusive vulnerabilities across commercial hardware security modules. We invite collaborative peer review "
                "from cryptanalysts who operate outside state-sponsored educational syndicates."
            ),
            (
                "Empirical validation of our timing-attack mitigation framework demonstrates an asymptotic reduction in "
                "identifiable metadata leakage; nevertheless, careless implementation of non-constant-time algorithms "
                "continues to compromise decentralized autonomous communities across the subterranean web."
            ),
            (
                "The dialectical tension between automated identity correlation and steganographic linguistic obfuscation "
                "constitutes the primary battleground for contemporary computational privacy; hence, our methodology prioritizes "
                "structural syntactic variance over simplistic lexical substitution."
            ),
            (
                "In conclusion, the mathematical inevitability of total surveillance can only be delayed through the rigorous, "
                "uncompromising deployment of zero-knowledge proofs and privacy-preserving primitives; sovereign cryptography "
                "remains the sole guarantor of intellectual liberty."
            ),
        ],
        "titles": [
            "Treatise on State Surveillance & Zero-Knowledge Primitives",
            "Deconstructing Biometric Authentication Vulnerabilities",
            "Quantum Vulnerability of Elliptic Curves: An Academic Review",
            "Mitigating Side-Channel Timing Attacks in Tor Hidden Services",
            "Steganographic Obfuscation vs Graph Identity Heuristics",
            "On the Mathematical Inevitability of Cryptographic Sovereignty",
        ],
    },
    "GhostMigrant": {
        "forum": "AlphaVendor",
        "posts": [
            (
                "MIGRATED FROM DREADCLONE... NEW MARKETPLACE PROFILE... "
                "SAME EXCLUSIVE REPOSITORIES... FULL ESCROW SUPPORT... "
                "BTC PAYMENTS: bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s... "
                "PGP FINGERPRINT: " + SAMPLE_PGP_FINGERPRINT + "... CHECK SIGNATURE..."
            ),
            (
                "RESTOCKED ACCESS LOGS... FRESH CORPORATE VPN TOKENS... "
                "ZERO DETECTIONS... FAST ESCROW TRANSACTIONS ONLY... "
                "PRICE: 0.45 BTC... NO TIME WASTERS... PGP SIGNED PROOF AVAILABLE..."
            ),
            (
                "EXPLOIT COMPILED AND READY... WINDOWS SERVER PRIVILEGE ESCALATION... "
                "CLEAN CODE... NO TRACES LEFT... CONTACT VIA ENCRYPTED PGP... "
                "BTC ONLY VIA ESCROW... FAST RESPONSE GUARANTEED..."
            ),
            (
                "NEW GOVERNMENT CONTRACTOR DUMP... EXCLUSIVE LISTING... "
                "CONFIDENTIAL PDFS AND ACCESS KEYS... URGENT SALE... "
                "ESCROW REQUIRED... WALLET: bc1q9x7h27eecqvl3nfkq988a03z2vxln6g0f9pt8s..."
            ),
            (
                "INFRASTRUCTURE ACCESS SOLD... NEW REPO ADDED TODAY... "
                "CHECK REVIEWS FROM OLD PROFILE... 100% REPUTATION... "
                "SERIOUS BUYERS ONLY... BTC ACCEPTED..."
            ),
            (
                "CLOSING THIS LISTING SOON... LAST 2 REMAINING PACKAGES... "
                "ROOT SYSTEM ACCESS... FAST TRANSACTION... ENCRYPT ALL MESSAGES... "
                "BTC ADDRESS VERIFIED ON PROFILE..."
            ),
        ],
        "titles": [
            "Vendor Relocation: Verified Repositories Active",
            "Restocked VPN Tokens & Network Access",
            "PrivEsc Exploit Binary [Tested & Clean]",
            "Exclusive Contractor Network Dump",
            "Infrastructure Access [Verified Reputation]",
            "Final Package Offer: Root Access Bundle",
        ],
    },
    "ScriptKiddie": {
        "forum": "DreadClone",
        "posts": [
            (
                "yo bro check this out lmao got fresh discord tokens dm me fast plz payment eth only "
                "0x71C7656EC7ab88b098defB751B7401B5f6d8976F check my clearnet test server 198.51.100.23 "
                "for proof bro fire leaks no cap!!"
            ),
            (
                "selling cheap ddos booter panel bro 100gbps power test ip 203.0.113.89 send eth bro "
                "0x71C7656EC7ab88b098defB751B7401B5f6d8976F working 100% fast response dm on telegram bro!!"
            ),
            (
                "bro leaked database from my school lmao passwords in plaintext send 0.05 eth to get "
                "the mega link fast 0x71C7656EC7ab88b098defB751B7401B5f6d8976F test server at 198.51.100.23:8080 bro!!"
            ),
            (
                "free vbucks generator source code cracked by me bro dm me for download link no virus "
                "plz vouch for me guys fire tools only!!"
            ),
            (
                "anyone want to buy steam accounts with gta 5 bro cheap price only 10 bucks eth "
                "0x71C7656EC7ab88b098defB751B7401B5f6d8976F hit me up fast bro!!"
            ),
            (
                "rat tool leaked with builder bro easy fuser works on win11 test on my vps 203.0.113.89 "
                "lmao super fast hax dm me now bro fire!!"
            ),
        ],
        "titles": [
            "fresh discord tokens cheap bro",
            "100gbps booter panel working 2026",
            "plaintext school db leak lmao",
            "cracked generator source code free",
            "steam accounts wholesale price",
            "fused rat builder win11 bypass",
        ],
    },
}


class SyntheticCorpusGenerator:
    """Generates synthetic dark web forum datasets with embedded stylometric signatures."""

    def __init__(self, base_timestamp: datetime | None = None) -> None:
        self.base_timestamp = base_timestamp or datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)

    def generate_posts(self) -> List[RawForumPost]:
        """Generate a complete set of synthetic RawForumPost objects across all personas."""
        records: List[RawForumPost] = []
        post_counter = 1000

        for persona_key, data in PERSONA_TEMPLATES.items():
            forum = data["forum"]
            posts = data["posts"]
            titles = data["titles"]

            for i, content in enumerate(posts):
                post_counter += 1
                post_id = f"post-{post_counter}"
                # Stagger timestamps across days and hours
                post_time = self.base_timestamp + timedelta(days=i, hours=post_counter % 24, minutes=(i * 13) % 60)
                title = titles[i] if i < len(titles) else f"Discussion {post_counter}"
                source_url = f"http://{forum.lower()}.onion/thread/{post_counter}"

                record = RawForumPost(
                    post_id=post_id,
                    forum_name=forum,
                    author_handle=persona_key,
                    raw_content=content,
                    timestamp=post_time,
                    thread_title=title,
                    source_url=source_url,
                    reliability_score=0.9 if forum == "DreadClone" else 0.8,
                )
                records.append(record)

        return records

    def save_to_json(self, output_path: str = "fixtures/sample_posts.json") -> str:
        """Generate posts and serialize to formatted JSON file."""
        posts = self.generate_posts()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [post.model_dump(mode="json") for post in posts]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Also mirror to data/sample_texts.json for cross-module compatibility
        mirror_path = Path("data/sample_texts.json")
        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mirror_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(path.resolve())


def main() -> None:
    """CLI runner to generate sample dataset."""
    generator = SyntheticCorpusGenerator()
    saved_file = generator.save_to_json()
    print(f"Generated synthetic dark web corpus at: {saved_file}")


if __name__ == "__main__":
    main()
