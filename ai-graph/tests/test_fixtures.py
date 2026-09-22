"""Tests verifying synthetic dark web fixtures, schema validity, and planted stylometric traits."""
import re
from pathlib import Path
from typing import List
import pytest

from schemas.raw_post import RawForumPost


def test_sample_posts_file_structure(sample_posts: List[RawForumPost]):
    """Verify sample_posts.json exists, has >= 20 posts, and parses into valid RawForumPost objects."""
    assert len(sample_posts) >= 20

    handles = {p.author_handle for p in sample_posts}
    assert handles == {"ShadowBroker", "CryptoRebel", "GhostMigrant", "ScriptKiddie"}

    forums = {p.forum_name for p in sample_posts}
    assert forums == {"DreadClone", "BreachNode", "AlphaVendor"}

    # Validate non-empty content and timestamps
    for post in sample_posts:
        assert len(post.raw_content) > 20
        assert post.timestamp is not None
        assert post.post_id.startswith("post-")


def test_persona_stylistic_overlap_between_a_and_c(sample_posts: List[RawForumPost]):
    """Verify Persona A (ShadowBroker) and Persona C (GhostMigrant) share planted stylistic traits while maintaining distinct handles."""
    persona_a_posts = [p for p in sample_posts if p.author_handle == "ShadowBroker"]
    persona_c_posts = [p for p in sample_posts if p.author_handle == "GhostMigrant"]

    assert len(persona_a_posts) >= 4
    assert len(persona_c_posts) >= 4

    # Trait 1: Distinct handles and distinct primary forums
    assert persona_a_posts[0].author_handle != persona_c_posts[0].author_handle
    assert persona_a_posts[0].forum_name != persona_c_posts[0].forum_name

    # Trait 2: Ellipses density (clipped writing habit)
    def count_ellipses(posts: List[RawForumPost]) -> float:
        total_ellipses = sum(p.raw_content.count("...") for p in posts)
        return total_ellipses / len(posts)

    a_ellipses = count_ellipses(persona_a_posts)
    c_ellipses = count_ellipses(persona_c_posts)

    assert a_ellipses >= 2.0, f"Expected Persona A to use frequent ellipses, got {a_ellipses}"
    assert c_ellipses >= 2.0, f"Expected Persona C to use frequent ellipses, got {c_ellipses}"
    # The two personas have closely overlapping ellipses frequency (within 2.0 of each other)
    assert abs(a_ellipses - c_ellipses) < 2.0

    # Trait 3: Capitalization ratio
    def uppercase_ratio(posts: List[RawForumPost]) -> float:
        total_upper = sum(sum(1 for c in p.raw_content if c.isupper()) for p in posts)
        total_alpha = sum(sum(1 for c in p.raw_content if c.isalpha()) for p in posts)
        return total_upper / max(total_alpha, 1)

    a_upper = uppercase_ratio(persona_a_posts)
    c_upper = uppercase_ratio(persona_c_posts)

    assert a_upper > 0.10, f"Persona A should have heavy capitalization, got {a_upper}"
    assert c_upper > 0.10, f"Persona C should have heavy capitalization, got {c_upper}"
    # Overlapping capitalization style (both heavy capitalization)
    assert abs(a_upper - c_upper) < 0.25

    # Trait 4: Average sentence length (clipped sentences)
    def avg_words_per_sentence(posts: List[RawForumPost]) -> float:
        sentence_lengths = []
        for p in posts:
            # Split sentences by ellipses and periods
            segments = [s.strip() for s in re.split(r"\.{3}|\.|\?", p.raw_content) if s.strip()]
            for s in segments:
                words = s.split()
                if words:
                    sentence_lengths.append(len(words))
        return sum(sentence_lengths) / max(len(sentence_lengths), 1)

    a_sent_len = avg_words_per_sentence(persona_a_posts)
    c_sent_len = avg_words_per_sentence(persona_c_posts)

    assert a_sent_len < 10.0, f"Persona A expected clipped sentences (<10 words), got {a_sent_len}"
    assert c_sent_len < 10.0, f"Persona C expected clipped sentences (<10 words), got {c_sent_len}"


def test_persona_b_academic_traits(sample_posts: List[RawForumPost]):
    """Verify Persona B (CryptoRebel) exhibits academic syntax (semicolons, long sentences) and Monero address."""
    persona_b_posts = [p for p in sample_posts if p.author_handle == "CryptoRebel"]
    assert len(persona_b_posts) >= 4

    # Semicolons used in academic prose
    semicolon_count = sum(p.raw_content.count(";") for p in persona_b_posts)
    assert semicolon_count >= 2, f"Persona B expected semicolons, got {semicolon_count}"

    # Monero address present
    all_content = " ".join(p.raw_content for p in persona_b_posts)
    assert re.search(r"4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}", all_content) is not None


def test_persona_d_script_kiddie_traits(sample_posts: List[RawForumPost]):
    """Verify Persona D (ScriptKiddie) exhibits repetitive slang, Ethereum address, and clearnet IP leakage."""
    persona_d_posts = [p for p in sample_posts if p.author_handle == "ScriptKiddie"]
    assert len(persona_d_posts) >= 4

    all_content = " ".join(p.raw_content for p in persona_d_posts).lower()
    assert "bro" in all_content
    assert "lmao" in all_content

    # Ethereum address present (0x + 40 hex chars)
    assert re.search(r"0x[a-fA-F0-9]{40}", all_content) is not None

    # Clearnet IP leakage present
    assert re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", all_content) is not None
