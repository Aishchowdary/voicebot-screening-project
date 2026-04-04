"""
AI Voicebot - Presale Bot
Main entry point for the LiveKit voice agent.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai as livekit_openai,
    deepgram,
    elevenlabs,
    silero,
)

from conversation_manager import ConversationManager
from scope_validator import ScopeValidator
from language_detector import LanguageDetector
from llm_processor import LLMProcessor

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class PresaleVoiceAgent(Agent):
    """LiveKit voice agent for presale conversations."""

    def __init__(self) -> None:
        super().__init__(instructions=self._build_system_prompt())
        self.conversation_manager = ConversationManager(scenario="presale")
        self.scope_validator = ScopeValidator(scenario="presale")
        self.language_detector = LanguageDetector()
        self.llm_processor = LLMProcessor(
            conversation_manager=self.conversation_manager,
            scope_validator=self.scope_validator,
            language_detector=self.language_detector,
        )

    def _build_system_prompt(self) -> str:
        """Load the presale system prompt from file."""
        prompt_path = os.path.join(
            os.path.dirname(__file__), "../config/prompts/presale_system_prompt.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Prompt file not found; using fallback prompt.")
            return (
                "You are a professional presale assistant. Speak naturally in Indian English. "
                "Help prospects understand the product, qualify their needs, and schedule demos. "
                "Never discuss pricing or close sales."
            )

    async def on_enter(self) -> None:
        """Called when the agent enters the room."""
        logger.info("Presale agent entered the room.")
        await self.session.say(
            "Namaste! Hello! Welcome. I'm your presale assistant. "
            "I'm here to help you learn more about our solutions and understand how we can help your business. "
            "You can speak with me in English or Hindi — whichever you're more comfortable with. "
            "So, tell me — what brings you here today?",
            allow_interruptions=True,
        )


async def entrypoint(ctx: agents.JobContext) -> None:
    """Main entrypoint for the LiveKit agent job."""
    logger.info("Starting presale voicebot agent...")

    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",  # multilingual model for English + Hindi
            detect_language=True,
        ),
        llm=livekit_openai.LLM(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.7,
        ),
        tts=elevenlabs.TTS(
            voice_id=os.getenv(
                "ELEVENLABS_VOICE_ID", "TX3LPaxmHKxFdv7VOQHJ"
            ),  # Indian English voice
            model_id="eleven_turbo_v2_5",
        ),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=PresaleVoiceAgent(),
        room_input_options=RoomInputOptions(),
    )

    logger.info("Presale voicebot session started successfully.")


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            worker_type=agents.WorkerType.ROOM,
        )
    )
