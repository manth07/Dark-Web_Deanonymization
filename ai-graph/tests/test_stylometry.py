"""Unit tests for classical stylometric feature extraction and edge case resilience."""
import pytest

from nlp.stylometry import StylometryExtractor
from schemas.extracted_features import StylometricFeatures


@pytest.fixture(scope="module")
def extractor() -> StylometryExtractor:
    """Fixture providing initialized StylometryExtractor instance."""
    return StylometryExtractor()


def test_distinct_features_between_clipped_and_academic_writing(extractor: StylometryExtractor):
    """Confirm distinct feature values between clipped dark web writing and verbose academic prose."""
    clipped_text = (
        "NEW SQL DUMP... 50K ACCOUNTS READY... NO TIME WASTERS. "
        "ESCROW ONLY... BTC PAYMENT REQUIRED... CONTACT VIA PGP NOW... "
        "PRICE IS 0.5 BTC... SERIOUS INQUIRIES ONLY..."
    )

    academic_text = (
        "The epistemological hegemony of centralized surveillance mechanisms inevitably "
        "demands a rigorous paradigm shift toward zero-knowledge mathematical primitives; "
        "furthermore, legacy transparency protocols fail catastrophically under adversarial graph analysis. "
        "A systematic deconstruction of modern biometric authentication infrastructures reveals profound "
        "architectural vulnerabilities; consequently, sovereign actors must deploy decentralized mixnets "
        "to preserve operational deniability and withstand state-sponsored cryptanalysis."
    )

    clipped_features = extractor.extract_features(clipped_text)
    academic_features = extractor.extract_features(academic_text)

    # 1. Sentence length: clipped writing has much shorter average sentence length
    assert clipped_features.average_sentence_length < 10.0
    assert academic_features.average_sentence_length > 15.0
    assert clipped_features.average_sentence_length < academic_features.average_sentence_length

    # 2. Uppercase ratio: clipped text uses heavy capitalization
    assert clipped_features.uppercase_ratio > 0.40
    assert academic_features.uppercase_ratio < 0.10
    assert clipped_features.uppercase_ratio > academic_features.uppercase_ratio

    # 3. Punctuation habits: ellipses in clipped, semicolons in academic
    assert clipped_features.punctuation_frequency.get("...", 0) >= 3
    assert academic_features.punctuation_frequency.get("...", 0) == 0

    assert academic_features.punctuation_frequency.get(";", 0) >= 2
    assert clipped_features.punctuation_frequency.get(";", 0) == 0

    # 4. Word length: academic prose has longer polysyllabic words
    assert academic_features.average_word_length > clipped_features.average_word_length


def test_edge_cases_zero_crashes(extractor: StylometryExtractor):
    """Verify zero crashes on empty strings, single words, emoji, unicode, and extreme garbage."""
    edge_cases = [
        "",  # Empty string
        "     \n\t  \r  ",  # Whitespace only
        "A",  # Single letter
        "exploit",  # Single word
        "!!!????....;;;:::",  # Pure punctuation
        "12345 67890 0x1234 999",  # Pure numbers/hex
        "Привет мир это тестовая строка для проверки",  # Non-English Cyrillic
        "这是一段没有空格的中文测试文本，验证模型不会崩溃",  # Chinese characters
        "🔥🚀💀👽👾💰💣💥",  # Emoji only
        "hello 🔥 world 🚀 deal 💰",  # Mixed text and emoji
        "a" * 5000,  # Single gigantic word
        ("word " * 2000),  # Very long repetitive text
        None,  # None type handled safely
    ]

    for case in edge_cases:
        # Should never raise exception, must return valid StylometricFeatures
        features = extractor.extract_features(case)  # type: ignore
        assert isinstance(features, StylometricFeatures)
        assert 0.0 <= features.uppercase_ratio <= 1.0
        assert 0.0 <= features.type_token_ratio <= 1.0
        assert 0.0 <= features.hapax_legomena_ratio <= 1.0
        assert features.character_count >= 0
        assert features.average_sentence_length >= 0.0
        assert features.average_word_length >= 0.0


def test_lexical_metric_accuracy(extractor: StylometryExtractor):
    """Verify mathematical correctness of TTR, hapax legomena, and sentence lengths on controlled text."""
    # 8 words total: "cat" appears twice, other 6 words appear once.
    # Words: the (1), quick (1), brown (1), fox (1), saw (1), the (2), black (1), cat (1)
    # Let's craft: "one two three four five six seven seven."
    # 8 tokens: 7 unique, 6 hapax ('one', 'two', 'three', 'four', 'five', 'six'), 'seven' occurs 2 times.
    controlled_text = "one two three four. five six seven seven."
    features = extractor.extract_features(controlled_text)

    # 8 words across 2 sentences => avg sentence length = 4.0
    assert features.average_sentence_length == 4.0

    # 7 unique words out of 8 => TTR = 7/8 = 0.875
    assert features.type_token_ratio == 0.875

    # 6 hapax words out of 8 => Hapax ratio = 6/8 = 0.75
    assert features.hapax_legomena_ratio == 0.75


def test_pos_and_function_word_distribution(extractor: StylometryExtractor):
    """Verify Part-of-Speech and function word frequencies are extracted on standard sentences."""
    text = "The quick brown fox jumps over the lazy dog."
    features = extractor.extract_features(text)

    assert len(features.pos_tag_distribution) > 0
    # Proportions should sum approximately to 1.0
    total_pos = sum(features.pos_tag_distribution.values())
    assert 0.95 <= total_pos <= 1.05

    # Function word 'the' appears twice out of 9 words
    assert "the" in features.function_word_frequency
    assert features.function_word_frequency["the"] > 0.15
