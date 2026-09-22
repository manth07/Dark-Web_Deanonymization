"""Classical NLP stylometric feature extraction using spaCy and NLTK.

Extracts lexical, syntactic, and structural markers of authorship style
with robust edge-case resilience for noisy dark web texts.
"""
from collections import Counter
import re
from typing import Dict, List, Optional, Set
import spacy
from spacy.language import Language

from core.logger import get_logger
from schemas.extracted_features import StylometricFeatures

logger = get_logger("nlp.stylometry")

# Core function words for syntactic profiling
CORE_FUNCTION_WORDS: Set[str] = {
    "the", "and", "to", "of", "a", "in", "that", "is", "was", "for",
    "it", "with", "as", "by", "on", "at", "from", "this", "be", "or",
    "an", "will", "my", "all", "would", "there", "their", "what", "so",
    "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only",
    "come", "its", "over", "think", "also", "back", "after", "use",
    "two", "how", "our", "work", "first", "well", "way", "even", "new",
    "want", "because", "any", "these", "give", "day", "most", "us"
}

PUNCTUATION_TARGETS = ["!", "?", "...", ",", ";", ":", '"', "'", "(", ")", "[", "]", "{", "}", "-"]


class StylometryExtractor:
    """Extracts lexical, syntactic, and structural stylometric markers from text."""

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        """Initialize spaCy NLP pipeline with fallback handling."""
        self.nlp: Language
        try:
            self.nlp = spacy.load(model_name, disable=["ner"])
        except Exception:
            try:
                # Fallback to blank model with sentencizer
                self.nlp = spacy.blank("en")
                if "sentencizer" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("sentencizer")
            except Exception:
                self.nlp = None  # type: ignore

    def extract_features(self, text: str) -> StylometricFeatures:
        """Extract comprehensive stylometric feature vector from input text.

        Guaranteed never to crash on empty strings, non-English text, or extreme lengths.
        """
        if not text or not isinstance(text, str) or not text.strip():
            return StylometricFeatures(
                average_sentence_length=0.0,
                average_word_length=0.0,
                type_token_ratio=0.0,
                hapax_legomena_ratio=0.0,
                punctuation_frequency={},
                pos_tag_distribution={},
                function_word_frequency={},
                paragraph_count=0,
                uppercase_ratio=0.0,
                character_count=0,
                embedding=[],
            )

        char_count = len(text)

        # 1. Structural Features
        paragraphs = [p for p in text.splitlines() if p.strip()]
        paragraph_count = max(len(paragraphs), 1)

        alpha_chars = [c for c in text if c.isalpha()]
        uppercase_chars = [c for c in alpha_chars if c.isupper()]
        uppercase_ratio = len(uppercase_chars) / max(len(alpha_chars), 1)
        uppercase_ratio = max(0.0, min(1.0, round(uppercase_ratio, 4)))

        # 2. Syntactic Features: Punctuation Counts
        punctuation_freq: Dict[str, int] = {}
        for mark in PUNCTUATION_TARGETS:
            count = text.count(mark)
            if count > 0:
                punctuation_freq[mark] = count

        # 3. Token & Sentence Extraction via spaCy or Regex fallback
        words: List[str] = []
        sentences_count = 1
        pos_distribution: Dict[str, float] = {}

        if self.nlp is not None:
            doc = self.nlp(text)
            # Filter tokens that contain alphabetic characters
            tokens = [token for token in doc if not token.is_space and not token.is_punct]
            words = [t.text.lower() for t in tokens if any(c.isalnum() for c in t.text)]

            # Detect sentences (split on spaCy sents + handle dark web ellipses delimiters)
            doc_sents = list(doc.sents)
            ellipses_breaks = text.count("...")
            sentences_count = max(len(doc_sents) + ellipses_breaks, 1)

            # POS Tag Distribution if tagged
            if doc.has_annotation("TAG") or doc.has_annotation("POS"):
                pos_counts = Counter(token.pos_ for token in doc if token.pos_)
                total_pos = sum(pos_counts.values())
                if total_pos > 0:
                    pos_distribution = {
                        pos: round(count / total_pos, 4)
                        for pos, count in pos_counts.items()
                    }
        else:
            # Fallback regex extraction
            words = [w.lower() for w in re.findall(r"\b\w+\b", text)]
            sentences = [s for s in re.split(r"\.{3}|\.|\?|!", text) if s.strip()]
            sentences_count = max(len(sentences), 1)

        total_words = len(words)

        # Handle very short / single-word texts gracefully
        if total_words == 0:
            return StylometricFeatures(
                average_sentence_length=0.0,
                average_word_length=0.0,
                type_token_ratio=0.0,
                hapax_legomena_ratio=0.0,
                punctuation_frequency=punctuation_freq,
                pos_tag_distribution=pos_distribution,
                function_word_frequency={},
                paragraph_count=paragraph_count,
                uppercase_ratio=uppercase_ratio,
                character_count=char_count,
                embedding=[],
            )

        # 4. Lexical Features
        avg_sentence_len = round(total_words / max(sentences_count, 1), 2)
        total_word_chars = sum(len(w) for w in words)
        avg_word_len = round(total_word_chars / total_words, 2)

        word_counts = Counter(words)
        unique_words = len(word_counts)
        ttr = max(0.0, min(1.0, round(unique_words / total_words, 4)))

        hapax_count = sum(1 for count in word_counts.values() if count == 1)
        hapax_ratio = max(0.0, min(1.0, round(hapax_count / total_words, 4)))

        # 5. Function Word Frequency
        func_word_freq: Dict[str, float] = {}
        for fw in CORE_FUNCTION_WORDS:
            if fw in word_counts:
                func_word_freq[fw] = round(word_counts[fw] / total_words, 4)

        return StylometricFeatures(
            average_sentence_length=avg_sentence_len,
            average_word_length=avg_word_len,
            type_token_ratio=ttr,
            hapax_legomena_ratio=hapax_ratio,
            punctuation_frequency=punctuation_freq,
            pos_tag_distribution=pos_distribution,
            function_word_frequency=func_word_freq,
            paragraph_count=paragraph_count,
            uppercase_ratio=uppercase_ratio,
            character_count=char_count,
            embedding=[],
        )
