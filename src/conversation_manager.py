"""
conversation_manager.py
Manages conversation state, history, context, and session metadata.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Literal, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

Language = Literal["en", "hi"]
Sentiment = Literal["positive", "neutral", "negative"]
Scenario = Literal["presale", "sales", "marketing"]


@dataclass
class Turn:
    """A single conversation turn."""
    role: Literal["user", "assistant"]
    content: str
    language: Language
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConversationContext:
    """Full conversation state object."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_language: Language = "en"
    language_history: list[Language] = field(default_factory=list)
    user_intent: str = ""
    entities_extracted: dict = field(default_factory=dict)
    conversation_history: list[Turn] = field(default_factory=list)
    scenario: Scenario = "presale"
    conversation_start_time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    turn_count: int = 0
    sentiment: Sentiment = "neutral"
    language_switch_count: int = 0
    scope_violations: int = 0
    topics_discussed: list[str] = field(default_factory=list)


class ConversationManager:
    """
    Manages multi-turn conversation state, language tracking,
    and entity extraction for the voicebot session.
    """

    def __init__(self, scenario: Scenario = "presale") -> None:
        self.context = ConversationContext(scenario=scenario)
        logger.info(
            "ConversationManager initialised | id=%s | scenario=%s",
            self.context.conversation_id,
            scenario,
        )

    # ------------------------------------------------------------------
    # Language management
    # ------------------------------------------------------------------

    def update_language(self, detected_language: Language) -> bool:
        """
        Update current language. Returns True if a switch occurred.
        """
        switched = detected_language != self.context.current_language
        if switched:
            self.context.language_switch_count += 1
            logger.info(
                "Language switch: %s → %s (switch #%d)",
                self.context.current_language,
                detected_language,
                self.context.language_switch_count,
            )
        self.context.language_history.append(self.context.current_language)
        self.context.current_language = detected_language
        return switched

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def add_user_turn(self, content: str, language: Optional[Language] = None) -> None:
        """Record a user message."""
        lang = language or self.context.current_language
        turn = Turn(role="user", content=content, language=lang)
        self.context.conversation_history.append(turn)
        self.context.turn_count += 1
        logger.debug("User turn #%d [%s]: %s", self.context.turn_count, lang, content[:80])

    def add_assistant_turn(self, content: str, language: Optional[Language] = None) -> None:
        """Record an assistant message."""
        lang = language or self.context.current_language
        turn = Turn(role="assistant", content=content, language=lang)
        self.context.conversation_history.append(turn)
        logger.debug("Assistant turn [%s]: %s", lang, content[:80])

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def get_openai_messages(self) -> list[dict]:
        """Return conversation history formatted for OpenAI chat completions."""
        return [
            {"role": t.role, "content": t.content}
            for t in self.context.conversation_history
        ]

    def update_sentiment(self, sentiment: Sentiment) -> None:
        self.context.sentiment = sentiment
        logger.debug("Sentiment updated to: %s", sentiment)

    def update_intent(self, intent: str) -> None:
        self.context.user_intent = intent

    def add_entity(self, key: str, value: str) -> None:
        self.context.entities_extracted[key] = value

    def record_topic(self, topic: str) -> None:
        if topic not in self.context.topics_discussed:
            self.context.topics_discussed.append(topic)

    def record_scope_violation(self) -> None:
        self.context.scope_violations += 1
        logger.warning(
            "Scope violation #%d recorded in conversation %s",
            self.context.scope_violations,
            self.context.conversation_id,
        )

    # ------------------------------------------------------------------
    # Summary / analytics
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """Return a summary dict for logging and analytics."""
        now = datetime.now(timezone.utc)
        start = datetime.fromisoformat(self.context.conversation_start_time)
        duration_seconds = (now - start).total_seconds()

        return {
            "conversation_id": self.context.conversation_id,
            "scenario": self.context.scenario,
            "duration_seconds": round(duration_seconds, 1),
            "turn_count": self.context.turn_count,
            "language_switch_count": self.context.language_switch_count,
            "final_language": self.context.current_language,
            "sentiment": self.context.sentiment,
            "scope_violations": self.context.scope_violations,
            "topics_discussed": self.context.topics_discussed,
            "entities_extracted": self.context.entities_extracted,
        }
