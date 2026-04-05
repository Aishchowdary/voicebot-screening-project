"""
stt_engine.py
Speech-to-Text engine wrapper supporting Deepgram (primary) with
a fallback structure for alternative providers.

Used for standalone testing and integration outside the LiveKit agent pipeline.
For the main LiveKit agent flow, STT is handled directly by the livekit-agents plugin.
"""

import asyncio
import logging
import os
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


class STTResult:
    """Holds a transcription result with metadata."""

    def __init__(
        self,
        transcript: str,
        is_final: bool,
        language: Optional[str] = None,
        confidence: float = 1.0,
    ) -> None:
        self.transcript = transcript
        self.is_final = is_final
        self.language = language  # e.g. "en-US", "hi-IN"
        self.confidence = confidence

    def __repr__(self) -> str:
        return (
            f"STTResult(is_final={self.is_final}, lang={self.language}, "
            f"confidence={self.confidence:.2f}, text='{self.transcript[:60]}')"
        )


class DeepgramSTTEngine:
    """
    Wrapper around Deepgram's async streaming API for multilingual STT.
    Supports English and Hindi with automatic language detection.
    """

    SUPPORTED_LANGUAGES = ["en", "hi"]
    MODEL = "nova-3"  # best multilingual accuracy on Deepgram

    def __init__(self) -> None:
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("DEEPGRAM_API_KEY environment variable not set.")
        self._client = None
        logger.info("DeepgramSTTEngine initialised (model=%s).", self.MODEL)

    def _get_client(self):
        """Lazy-load Deepgram client."""
        if self._client is None:
            try:
                from deepgram import DeepgramClient
                self._client = DeepgramClient(self.api_key)
            except ImportError as exc:
                raise ImportError(
                    "deepgram-sdk not installed. Run: pip install deepgram-sdk"
                ) from exc
        return self._client

    async def transcribe_file(self, audio_path: str) -> STTResult:
        """
        Transcribe a local audio file (wav/mp3/flac) using Deepgram.
        Useful for testing without a live audio stream.
        """
        client = self._get_client()
        try:
            from deepgram import PrerecordedOptions, FileSource

            with open(audio_path, "rb") as audio_file:
                buffer_data = audio_file.read()

            payload: FileSource = {"buffer": buffer_data}
            options = PrerecordedOptions(
                model=self.MODEL,
                detect_language=True,
                smart_format=True,
                punctuate=True,
                language="multi",
            )

            response = await asyncio.to_thread(
                client.listen.prerecorded.v("1").transcribe_file,
                payload,
                options,
            )

            result = response["results"]["channels"][0]["alternatives"][0]
            detected_lang = (
                response["results"]["channels"][0]
                .get("detected_language", "en")
                .split("-")[0]
            )
            return STTResult(
                transcript=result["transcript"],
                is_final=True,
                language=detected_lang,
                confidence=result.get("confidence", 1.0),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Deepgram file transcription failed: %s", exc)
            raise

    async def stream_transcription(
        self, audio_chunks: AsyncIterator[bytes]
    ) -> AsyncIterator[STTResult]:
        """
        Stream audio chunks to Deepgram and yield STTResult objects.
        Used for real-time transcription in non-LiveKit contexts.
        """
        client = self._get_client()
        try:
            from deepgram import LiveOptions, LiveTranscriptionEvents

            options = LiveOptions(
                model=self.MODEL,
                language="multi",
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
            )

            results_queue: asyncio.Queue[STTResult] = asyncio.Queue()

            dg_connection = client.listen.asynclive.v("1")

            async def on_transcript(self_inner, result, **kwargs):  # noqa: ARG001
                sentence = result.channel.alternatives[0].transcript
                is_final = result.is_final
                if sentence:
                    await results_queue.put(
                        STTResult(
                            transcript=sentence,
                            is_final=is_final,
                            language=result.channel.detected_language or "en",
                            confidence=result.channel.alternatives[0].confidence,
                        )
                    )

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)
            await dg_connection.start(options)

            async def send_audio():
                async for chunk in audio_chunks:
                    await dg_connection.send(chunk)
                await dg_connection.finish()
                await results_queue.put(None)  # sentinel

            asyncio.create_task(send_audio())

            while True:
                item = await results_queue.get()
                if item is None:
                    break
                yield item

        except Exception as exc:  # noqa: BLE001
            logger.error("Deepgram streaming failed: %s", exc)
            raise
