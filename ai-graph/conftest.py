"""Pytest configuration and shared fixtures for the stylometry and graph intelligence engine."""
import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from fixtures.synthetic_generator import SyntheticCorpusGenerator
from schemas.raw_post import RawForumPost


@pytest.fixture(scope="session")
def sample_posts_file(tmp_path_factory) -> Path:
    """Ensure fixtures/sample_posts.json exists and return its path."""
    fixture_path = Path("fixtures/sample_posts.json")
    if not fixture_path.exists():
        generator = SyntheticCorpusGenerator()
        generator.save_to_json(str(fixture_path))
    return fixture_path


@pytest.fixture
def sample_posts(sample_posts_file: Path) -> List[RawForumPost]:
    """Provide synthetic dark web posts parsed as RawForumPost instances."""
    with open(sample_posts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [RawForumPost.model_validate(item) for item in data]


@pytest.fixture
def sample_posts_raw(sample_posts_file: Path) -> List[Dict[str, Any]]:
    """Provide synthetic dark web posts as raw dictionaries."""
    with open(sample_posts_file, "r", encoding="utf-8") as f:
        return json.load(f)
