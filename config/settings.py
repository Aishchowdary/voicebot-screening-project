"""
config/settings.py
Centralised configuration loaded from environment variables and YAML config files.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent
SCENARIOS_DIR = CONFIG_DIR / "scenarios"
PROMPTS_DIR = CONFIG_DIR / "prompts"


def _load_yaml(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("Config file not found: %s", path)
        return {}


@dataclass
class LiveKitSettings:
    url: str = field(default_factory=lambda: os.getenv("LIVEKIT_URL", ""))
    api_key: str = field(default_factory=lambda: os.getenv("LIVEKIT_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("LIVEKIT_API_SECRET", ""))


@dataclass
class STTSettings:
    provider: str = "deepgram"
    model: str = "nova-3"
    language: str = "multi"
    detect_language: bool = True
    api_key: str = field(default_factory=lambda: os.getenv("DEEPGRAM_API_KEY", ""))


@dataclass
class LLMSettings:
    provider: str = "openai"
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    temperature: float = 0.7
    max_tokens: int = 300
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))


@dataclass
class TTSSettings:
    provider: str = "elevenlabs"
    voice_id: str = field(
        default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", "TX3LPaxmHKxFdv7VOQHJ")
    )
    model_id: str = "eleven_turbo_v2_5"
    api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    hindi_provider: str = "elevenlabs"
    sarvam_api_key: str = field(default_factory=lambda: os.getenv("SARVAM_API_KEY", ""))


@dataclass
class AppSettings:
    scenario: Literal["presale", "sales", "marketing"] = "presale"
    log_level: str = "INFO"
    log_dir: str = "logs/"
    livekit: LiveKitSettings = field(default_factory=LiveKitSettings)
    stt: STTSettings = field(default_factory=STTSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    tts: TTSSettings = field(default_factory=TTSSettings)


def load_settings(scenario: str = "presale") -> AppSettings:
    """Load settings from YAML and environment variables."""
    yaml_data = _load_yaml(SCENARIOS_DIR / f"{scenario}_config.yaml")

    settings = AppSettings(
        scenario=scenario,  # type: ignore[arg-type]
        log_level=yaml_data.get("logging", {}).get("level", "INFO"),
        log_dir=yaml_data.get("logging", {}).get("log_dir", "logs/"),
    )

    # Override with YAML values where present
    stt_yaml = yaml_data.get("stt", {})
    settings.stt.model = stt_yaml.get("model", settings.stt.model)
    settings.stt.detect_language = stt_yaml.get("detect_language", True)

    llm_yaml = yaml_data.get("llm", {})
    settings.llm.model = llm_yaml.get("model", settings.llm.model)
    settings.llm.temperature = llm_yaml.get("temperature", settings.llm.temperature)
    settings.llm.max_tokens = llm_yaml.get("max_tokens", settings.llm.max_tokens)

    tts_yaml = yaml_data.get("tts", {})
    settings.tts.provider = tts_yaml.get("provider", settings.tts.provider)
    settings.tts.model_id = tts_yaml.get("model_id", settings.tts.model_id)
    settings.tts.hindi_provider = tts_yaml.get("hindi_provider", "elevenlabs")

    logger.info("Settings loaded for scenario: %s", scenario)
    return settings
