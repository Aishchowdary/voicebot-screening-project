"""
tests/test_stt.py
Unit tests for the STT engine module.
"""

import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from stt_engine import STTResult


class TestSTTResult:
    """Tests for the STTResult data class."""

    def test_basic_creation(self):
        result = STTResult(
            transcript="Hello, how are you?",
            is_final=True,
            language="en",
            confidence=0.98,
        )
        assert result.transcript == "Hello, how are you?"
        assert result.is_final is True
        assert result.language == "en"
        assert result.confidence == 0.98

    def test_repr(self):
        result = STTResult(transcript="Test", is_final=False, language="hi", confidence=0.9)
        r = repr(result)
        assert "is_final=False" in r
        assert "hi" in r

    def test_low_confidence(self):
        result = STTResult(transcript="unclear speech", is_final=True, confidence=0.4)
        assert result.confidence < 0.5

    def test_empty_transcript(self):
        result = STTResult(transcript="", is_final=False)
        assert result.transcript == ""

    def test_hindi_transcript(self):
        result = STTResult(
            transcript="नमस्ते, आप कैसे हैं?",
            is_final=True,
            language="hi",
            confidence=0.95,
        )
        assert "नमस्ते" in result.transcript
        assert result.language == "hi"


class TestDeepgramSTTEngineInit:
    """Tests for DeepgramSTTEngine initialisation (no API calls)."""

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
        from stt_engine import DeepgramSTTEngine
        with pytest.raises(EnvironmentError, match="DEEPGRAM_API_KEY"):
            DeepgramSTTEngine()

    def test_init_with_key(self, monkeypatch):
        monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key-123")
        from stt_engine import DeepgramSTTEngine
        engine = DeepgramSTTEngine()
        assert engine.api_key == "test-key-123"
        assert engine.MODEL == "nova-3"
