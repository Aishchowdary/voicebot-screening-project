"""
llm_processor.py
Handles all LLM interactions including context management,
scope validation, language-aware prompting, and response generation.
"""

import logging
import os
from typing import Optional

from openai import AsyncOpenAI

from conversation_manager import ConversationManager
from scope_validator import ScopeValidator
from language_detector import LanguageDetector

logger = logging.getLogger(__name__)


LANGUAGE_INSTRUCTION: dict[str, str] = {
    "en": (
        "Respond in English only. Use Indian English phrasing naturally — "
        "warm, professional, and respectful."
    ),
    "hi": (
        "Respond in Hindi (Devanagari script). Use polite and formal Hindi. "
        "It's acceptable to mix in occasional English technical terms naturally."
    ),
}

SENTIMENT_CONTEXT: dict[str, str] = {
    "positive": "The user seems engaged and positive. Match their energy warmly.",
    "neutral": "The user is neutral. Be professional and informative.",
    "negative": "The user may be frustrated or sceptical. Be extra patient, empathetic, and helpful.",
}


class LLMProcessor:
    """
    Wraps OpenAI async client with conversation context, language awareness,
    and scope validation built in.
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        scope_validator: ScopeValidator,
        language_detector: LanguageDetector,
        model: Optional[str] = None,
    ) -> None:
        self.cm = conversation_manager
        self.sv = scope_validator
        self.ld = language_detector
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("LLMProcessor initialised | model=%s", self.model)

    async def process(self, user_text: str) -> str:
        """
        Full pipeline:
        1. Detect language (including explicit switch requests).
        2. Check user query scope.
        3. Build messages and call LLM.
        4. Validate LLM response scope.
        5. Return final response.
        """
        # -- 1. Language detection ------------------------------------------
        explicit_switch = self.ld.is_language_switch_requested(user_text)
        if explicit_switch:
            language = explicit_switch
        else:
            language = self.ld.detect(user_text)
        self.cm.update_language(language)
        self.cm.add_user_turn(user_text, language)

        # -- 2. Scope check on user input -----------------------------------
        redirect = self.sv.validate_and_redirect(user_text, language)
        if redirect:
            self.cm.record_scope_violation()
            self.cm.add_assistant_turn(redirect, language)
            logger.info("User query out of scope; returning redirect.")
            return redirect

        # -- 3. Build messages ----------------------------------------------
        messages = self._build_messages(language)

        # -- 4. Call LLM ----------------------------------------------------
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
            )
            assistant_text = response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM call failed: %s", exc)
            assistant_text = self._fallback_response(language)

        # -- 5. Scope check on LLM output -----------------------------------
        output_redirect = self.sv.validate_and_redirect(assistant_text, language)
        if output_redirect:
            self.cm.record_scope_violation()
            logger.warning("LLM response was out of scope; replacing with redirect.")
            assistant_text = output_redirect

        self.cm.add_assistant_turn(assistant_text, language)
        return assistant_text

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_messages(self, language: str) -> list[dict]:
        """Construct the messages array for the OpenAI API call."""
        # Dynamic addendum injected at the END of the system prompt
        lang_instruction = LANGUAGE_INSTRUCTION.get(language, LANGUAGE_INSTRUCTION["en"])
        sentiment_hint = SENTIMENT_CONTEXT.get(
            self.cm.context.sentiment, SENTIMENT_CONTEXT["neutral"]
        )
        addendum = (
            f"\n\n---\nCurrent language preference: {language.upper()}. "
            f"{lang_instruction}\n"
            f"Sentiment context: {sentiment_hint}\n"
            f"Turn #{self.cm.context.turn_count}. Keep responses concise (≤3 sentences) "
            "unless the user asks for more detail."
        )

        # Grab the base system prompt from conversation manager's scenario
        base_system = self._load_system_prompt()
        system_message = {"role": "system", "content": base_system + addendum}

        history = self.cm.get_openai_messages()
        return [system_message] + history

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), "../config/prompts/presale_system_prompt.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return (
                "You are a professional presale voicebot. Help prospects understand "
                "the product, qualify leads, and schedule demos. Never discuss pricing."
            )

    @staticmethod
    def _fallback_response(language: str) -> str:
        if language == "hi":
            return (
                "Maafi chahta hoon, abhi thodi technical dikkat aa rahi hai. "
                "Kya aap thodi der mein dobara try kar sakte hain?"
            )
        return (
            "I apologise — I'm experiencing a brief technical issue. "
            "Could you give me just a moment and try again?"
        )
