"""
tests/test_language_switching.py
Tests for LanguageDetector and ConversationManager language handling.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from language_detector import LanguageDetector, _contains_devanagari, _hinglish_score
from conversation_manager import ConversationManager


class TestDevanagariDetection:
    def test_pure_devanagari(self):
        assert _contains_devanagari("नमस्ते आप कैसे हैं") is True

    def test_mixed_devanagari_latin(self):
        assert _contains_devanagari("Hello नमस्ते") is True

    def test_pure_latin(self):
        assert _contains_devanagari("Hello, how are you?") is False

    def test_empty_string(self):
        assert _contains_devanagari("") is False


class TestHinglishScore:
    def test_pure_english(self):
        score = _hinglish_score("What are the main features of your product?")
        assert score == 0.0

    def test_obvious_hinglish(self):
        score = _hinglish_score("haan main jaanta hoon aap kya bol rahe hain")
        assert score >= 0.2

    def test_mixed(self):
        score = _hinglish_score("namaste I want to know about your product")
        assert 0 < score < 1.0

    def test_empty(self):
        assert _hinglish_score("") == 0.0


class TestLanguageDetector:
    def setup_method(self):
        self.detector = LanguageDetector()

    def test_devanagari_detected_as_hindi(self):
        assert self.detector.detect("नमस्ते, मुझे आपके product के बारे में जानना है") == "hi"

    def test_english_detected(self):
        assert self.detector.detect("Hello, I would like to know about your product.") == "en"

    def test_hinglish_detected_as_hindi(self):
        result = self.detector.detect("haan main samajh gaya aur mujhe jaanna hai")
        assert result == "hi"

    def test_empty_string_defaults_to_english(self):
        assert self.detector.detect("") == "en"

    def test_whitespace_defaults_to_english(self):
        assert self.detector.detect("   ") == "en"

    def test_explicit_english_switch_en(self):
        result = self.detector.is_language_switch_requested("English please")
        assert result == "en"

    def test_explicit_english_switch_en2(self):
        result = self.detector.is_language_switch_requested("can we speak english")
        assert result == "en"

    def test_explicit_hindi_switch(self):
        result = self.detector.is_language_switch_requested("hindi mein boliye")
        assert result == "hi"

    def test_no_explicit_switch(self):
        result = self.detector.is_language_switch_requested("Tell me more about your product")
        assert result is None


class TestConversationManagerLanguage:
    def setup_method(self):
        self.cm = ConversationManager(scenario="presale")

    def test_initial_language_is_english(self):
        assert self.cm.context.current_language == "en"

    def test_update_language_no_switch(self):
        switched = self.cm.update_language("en")
        assert switched is False

    def test_update_language_switch(self):
        switched = self.cm.update_language("hi")
        assert switched is True
        assert self.cm.context.current_language == "hi"
        assert self.cm.context.language_switch_count == 1

    def test_multiple_switches(self):
        self.cm.update_language("hi")
        self.cm.update_language("en")
        self.cm.update_language("hi")
        assert self.cm.context.language_switch_count == 3

    def test_language_history_tracked(self):
        self.cm.update_language("hi")
        self.cm.update_language("en")
        assert "en" in self.cm.context.language_history
        assert "hi" in self.cm.context.language_history
