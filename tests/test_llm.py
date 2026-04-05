"""
tests/test_llm.py
Unit tests for the LLM processor and related helpers.
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from conversation_manager import ConversationManager
from scope_validator import ScopeValidator
from language_detector import LanguageDetector
from llm_processor import LLMProcessor, LANGUAGE_INSTRUCTION


class TestLLMProcessorInit:
    def test_init_requires_openai_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        cm = ConversationManager()
        sv = ScopeValidator()
        ld = LanguageDetector()
        processor = LLMProcessor(cm, sv, ld)
        assert processor.model == "gpt-4o" or processor.model is not None

    def test_language_instructions_keys(self):
        assert "en" in LANGUAGE_INSTRUCTION
        assert "hi" in LANGUAGE_INSTRUCTION


class TestLLMProcessorFallback:
    def test_fallback_english(self):
        text = LLMProcessor._fallback_response("en")
        assert "apologise" in text.lower() or "sorry" in text.lower() or "technical" in text.lower()

    def test_fallback_hindi(self):
        text = LLMProcessor._fallback_response("hi")
        assert len(text) > 10  # non-empty Hindi response

    def test_fallback_unknown_language(self):
        # Unknown language should fall back to English-like response
        text = LLMProcessor._fallback_response("xx")
        assert isinstance(text, str)
        assert len(text) > 0


class TestLLMProcessorScopeRedirect:
    """Test that out-of-scope queries are redirected without calling the LLM."""

    @pytest.mark.asyncio
    async def test_pricing_query_redirected(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        cm = ConversationManager(scenario="presale")
        sv = ScopeValidator(scenario="presale")
        ld = LanguageDetector()

        processor = LLMProcessor(cm, sv, ld)

        # Patch OpenAI client so it never actually gets called
        mock_create = AsyncMock()
        processor.client.chat.completions.create = mock_create

        response = await processor.process("What is the price of your product?")

        # Should return a redirect, not call the LLM
        mock_create.assert_not_called()
        assert isinstance(response, str)
        assert len(response) > 0
        assert cm.context.scope_violations == 1

    @pytest.mark.asyncio
    async def test_in_scope_query_calls_llm(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        cm = ConversationManager(scenario="presale")
        sv = ScopeValidator(scenario="presale")
        ld = LanguageDetector()

        processor = LLMProcessor(cm, sv, ld)

        # Mock LLM response
        mock_message = MagicMock()
        mock_message.content = "Great! Let me tell you about our product capabilities."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        processor.client.chat.completions.create = AsyncMock(return_value=mock_response)

        response = await processor.process("Can you tell me about your product features?")

        processor.client.chat.completions.create.assert_called_once()
        assert response == "Great! Let me tell you about our product capabilities."
        assert cm.context.scope_violations == 0
