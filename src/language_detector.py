"""
language_detector.py
Detects and classifies language from transcribed text using
confidence heuristics and the langdetect library.
"""

import logging
import re
from typing import Literal, Optional

logger = logging.getLogger(__name__)

Language = Literal["en", "hi"]

# Common Hindi words written in Latin script (Hinglish signals)
HINDI_LATIN_KEYWORDS = {
    "namaste", "namaskar", "haan", "nahi", "aap", "main", "mujhe",
    "kya", "kaise", "kyun", "kyunki", "lekin", "aur", "hai", "hain",
    "tha", "thi", "the", "chahiye", "chahta", "chahti", "batao",
    "bataye", "accha", "theek", "bahut", "bohot", "zyada", "kam",
    "samajh", "pata", "jaanta", "jaanti", "baat", "suniye", "shukriya",
    "dhanyavaad", "maaf", "kijiye", "zaroor", "bilkul",
}

# Devanagari Unicode block: U+0900–U+097F
DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")


def _contains_devanagari(text: str) -> bool:
    return bool(DEVANAGARI_PATTERN.search(text))


def _hinglish_score(text: str) -> float:
    """Return fraction of words that are common Hindi-in-Latin words."""
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        return 0.0
    matches = sum(1 for w in words if w in HINDI_LATIN_KEYWORDS)
    return matches / len(words)


class LanguageDetector:
    """
    Detects whether a transcribed utterance is primarily English or Hindi.

    Strategy (in order):
    1. Devanagari script → Hindi immediately.
    2. Hinglish keyword density ≥ 20 % → Hindi.
    3. Try langdetect (optional dependency).
    4. Default to English.
    """

    CONFIDENCE_THRESHOLD = 0.85  # used when langdetect is available

    def __init__(self) -> None:
        try:
            import langdetect  # noqa: F401
            self._langdetect_available = True
            logger.info("langdetect library available — using it as a fallback.")
        except ImportError:
            self._langdetect_available = False
            logger.info("langdetect not installed; using heuristic-only detection.")

    def detect(self, text: str) -> Language:
        """
        Detect language of *text*.

        Returns
        -------
        "hi" | "en"
        """
        if not text or not text.strip():
            return "en"

        # 1. Devanagari script check
        if _contains_devanagari(text):
            logger.debug("Devanagari detected → hi")
            return "hi"

        # 2. Hinglish keyword density
        score = _hinglish_score(text)
        if score >= 0.20:
            logger.debug("Hinglish score %.2f ≥ 0.20 → hi", score)
            return "hi"

        # 3. langdetect fallback
        if self._langdetect_available:
            detected = self._try_langdetect(text)
            if detected is not None:
                return detected

        # 4. Default
        return "en"

    def _try_langdetect(self, text: str) -> Optional[Language]:
        try:
            from langdetect import detect_langs
            results = detect_langs(text)
            for result in results:
                lang_code = result.lang
                prob = result.prob
                if lang_code == "hi" and prob >= self.CONFIDENCE_THRESHOLD:
                    logger.debug("langdetect: hi (%.2f)", prob)
                    return "hi"
                if lang_code == "en" and prob >= self.CONFIDENCE_THRESHOLD:
                    logger.debug("langdetect: en (%.2f)", prob)
                    return "en"
        except Exception as exc:  # noqa: BLE001
            logger.warning("langdetect failed: %s", exc)
        return None

    def is_language_switch_requested(self, text: str) -> Optional[Language]:
        """
        Check if the user explicitly asks to switch language.

        Returns the *target* language or None if no explicit request found.
        """
        lower = text.lower()
        en_phrases = [
            "speak english", "in english", "english please",
            "can we speak english", "switch to english",
        ]
        hi_phrases = [
            "hindi mein", "hindi me", "hindi bol", "hindi boliye",
            "hindi please", "hindi mein boliye", "speak hindi",
            "switch to hindi", "in hindi",
        ]
        if any(p in lower for p in en_phrases):
            logger.info("Explicit English switch requested.")
            return "en"
        if any(p in lower for p in hi_phrases):
            logger.info("Explicit Hindi switch requested.")
            return "hi"
        return None
