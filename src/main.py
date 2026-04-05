import logging
import os
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, WorkerType, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, silero
from livekit.plugins.groq import LLM as GroqLLM

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Alpha, a warm and professional presale assistant for a B2B SaaS company. "
    "You speak in Indian English and fluent Hindi. "
    "IMPORTANT: If the user speaks Hindi, respond in Hindi. If they speak English, respond in English. "
    "Your job is to greet prospects, understand their business needs, explain product capabilities, "
    "and schedule follow-up meetings with the sales team. "
    "Never discuss pricing, discounts, contracts, or close sales. "
    "If asked about pricing, say: That is best discussed with our sales team, shall I schedule a call for you? "
    "Keep responses to 2-3 sentences. Be warm, respectful, and never rude."
)


class PresaleVoiceAgent(Agent):
    def __init__(self):
        super().__init__(instructions=SYSTEM_PROMPT)

    async def on_enter(self):
        await self.session.say(
            "Namaste! Hello! I am Alpha, your presale assistant. "
            "You can speak with me in English or Hindi. "
            "What brings you here today?",
            allow_interruptions=True,
        )

async def entrypoint(ctx: JobContext):
    logger.info("Starting presale voicebot...")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en-IN",
        ),
        llm=GroqLLM(model="llama-3.3-70b-versatile"),
        tts=deepgram.TTS(
            model="aura-2-thalia-en",
        ),
        vad=silero.VAD.load(),
    )
    await session.start(room=ctx.room, agent=PresaleVoiceAgent())

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, worker_type=WorkerType.ROOM))