"""
tts_engine.py
Text-to-Speech engine supporting ElevenLabs (primary) with Indian English accent
and Sarvam AI as an alternative for native Hindi output.
"""

import asyncio
import logging
import os
from typing import Literal, Optional

logger = logging.getLogger(__name__)

Language = Literal["en", "hi"]


class TTSResult:
    """Holds synthesised audio bytes."""

    def __init__(self, audio_bytes: bytes, language: Language, text: str) -> None:
        self.audio_bytes = audio_bytes
        self.language = language
        self.text = text
        self.size_kb = round(len(audio_bytes) / 1024, 1)

    def __repr__(self) -> str:
        return f"TTSResult(lang={self.language}, size={self.size_kb}KB)"


class ElevenLabsTTSEngine:
    """
    ElevenLabs TTS engine with Indian English voice.
    Falls back to a placeholder for non-English when Sarvam is unavailable.
    """

    # ElevenLabs voice IDs - update in .env or config as needed
    DEFAULT_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"  # Indian English voice
    MODEL_ID = "eleven_turbo_v2_5"  # low-latency model

    VOICE_SETTINGS = {
        "stability": 0.55,
        "similarity_boost": 0.80,
        "style": 0.25,
        "use_speaker_boost": True,
    }

    def __init__(self, voice_id: Optional[str] = None) -> None:
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise EnvironmentError("ELEVENLABS_API_KEY environment variable not set.")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", self.DEFAULT_VOICE_ID)
        self._client = None
        logger.info("ElevenLabsTTSEngine initialised | voice=%s", self.voice_id)

    def _get_client(self):
        if self._client is None:
            try:
                from elevenlabs.client import AsyncElevenLabs
                self._client = AsyncElevenLabs(api_key=self.api_key)
            except ImportError as exc:
                raise ImportError(
                    "elevenlabs SDK not installed. Run: pip install elevenlabs"
                ) from exc
        return self._client

    async def synthesise(self, text: str, language: Language = "en") -> TTSResult:
        """
        Convert *text* to speech audio bytes.
        For Hindi, applies slower speech rate and slightly different stability.
        """
        client = self._get_client()
        settings = dict(self.VOICE_SETTINGS)

        if language == "hi":
            # Slightly more stable output for Hindi transliteration
            settings["stability"] = 0.65

        try:
            audio_stream = client.generate(
                text=text,
                voice=self.voice_id,
                model=self.MODEL_ID,
                voice_settings=settings,
            )
            audio_bytes = b""
            async for chunk in audio_stream:
                audio_bytes += chunk

            logger.debug("TTS synthesised %d bytes for lang=%s", len(audio_bytes), language)
            return TTSResult(audio_bytes=audio_bytes, language=language, text=text)

        except Exception as exc:  # noqa: BLE001
            logger.error("ElevenLabs TTS failed: %s", exc)
            raise

    async def synthesise_to_file(
        self, text: str, output_path: str, language: Language = "en"
    ) -> str:
        """Synthesise speech and save to a .mp3 file. Returns the path."""
        result = await self.synthesise(text, language)
        with open(output_path, "wb") as f:
            f.write(result.audio_bytes)
        logger.info("TTS audio saved to %s (%s KB)", output_path, result.size_kb)
        return output_path


class SarvamTTSEngine:
    """
    Sarvam AI TTS engine — best for native Hindi speech.
    Use as a drop-in alternative or in combination with ElevenLabs for Hindi.
    """

    BASE_URL = "https://api.sarvam.ai/text-to-speech"
    DEFAULT_SPEAKER = "meera"  # Hindi female voice
    TARGET_LANGUAGE = "hi-IN"

    def __init__(self) -> None:
        self.api_key = os.getenv("SARVAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("SARVAM_API_KEY environment variable not set.")
        logger.info("SarvamTTSEngine initialised (speaker=%s).", self.DEFAULT_SPEAKER)

    async def synthesise(self, text: str) -> TTSResult:
        """Synthesise Hindi text using Sarvam AI API."""
        import aiohttp

        payload = {
            "inputs": [text],
            "target_language_code": self.TARGET_LANGUAGE,
            "speaker": self.DEFAULT_SPEAKER,
            "pace": 1.0,
            "enable_preprocessing": True,
        }
        headers = {
            "Content-Type": "application/json",
            "API-Subscription-Key": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.BASE_URL, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        import base64
        audio_b64 = data["audios"][0]
        audio_bytes = base64.b64decode(audio_b64)
        logger.debug("Sarvam TTS synthesised %d bytes", len(audio_bytes))
        return TTSResult(audio_bytes=audio_bytes, language="hi", text=text)
