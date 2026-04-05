# Architecture

## System Overview

The voicebot is built on the **LiveKit Agents** framework, which provides the real-time WebRTC voice pipeline. The agent runs as a single Python process that joins a LiveKit room and handles the full STT → LLM → TTS loop.

```
User (browser / phone)
        │  WebRTC audio
        ▼
┌─────────────────────────────────┐
│         LiveKit Cloud           │
│   (room + media relay/SFU)      │
└────────────┬────────────────────┘
             │ audio frames
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  LiveKit Agent Worker (Python)               │
│                                                             │
│  ┌──────────────┐   raw text    ┌──────────────────────┐   │
│  │  Deepgram    │ ────────────► │  LanguageDetector    │   │
│  │  STT Engine  │               │  (heuristic + lib)   │   │
│  └──────────────┘               └──────────┬───────────┘   │
│                                            │ language tag   │
│                                            ▼               │
│                                 ┌──────────────────────┐   │
│                                 │  ScopeValidator       │   │
│                                 │  (pattern matching)   │   │
│                                 └──────────┬───────────┘   │
│                                            │ validated text │
│                                            ▼               │
│                                 ┌──────────────────────┐   │
│                                 │  LLMProcessor         │   │
│                                 │  (OpenAI GPT-4o)      │   │
│                                 └──────────┬───────────┘   │
│                                            │ response text  │
│                                            ▼               │
│                                 ┌──────────────────────┐   │
│                                 │  ScopeValidator       │   │
│                                 │  (output guard)       │   │
│                                 └──────────┬───────────┘   │
│                                            │ safe text      │
│                                            ▼               │
│                                 ┌──────────────────────┐   │
│                                 │  ElevenLabs TTS       │   │
│                                 │  (Indian English)     │   │
│                                 └──────────┬───────────┘   │
│                                            │ audio stream   │
└────────────────────────────────────────────┼───────────────┘
                                             │
                                             ▼
                                     User hears response
```

## Component Descriptions

### `main.py` — Agent Entry Point
- Initialises the LiveKit `AgentSession` with STT, LLM, TTS, and VAD plugins.
- Defines `PresaleVoiceAgent` (subclass of `Agent`) which owns the greeting and lifecycle hooks.
- Runs via `livekit.agents.cli` which manages worker registration, room assignment, and graceful shutdown.

### `conversation_manager.py` — State Machine
- Holds the full `ConversationContext` dataclass (language, history, entities, sentiment, analytics).
- Tracks every user and assistant turn with timestamps and language tags.
- Exposes `get_openai_messages()` to format history for the OpenAI API.
- Provides `get_summary()` for post-call logging and analytics.

### `language_detector.py` — Language Classification
- **Step 1**: Devanagari Unicode check — immediate Hindi signal.
- **Step 2**: Hinglish keyword density — catches Latin-script Hindi (Hinglish).
- **Step 3**: `langdetect` library (optional) for additional confidence.
- **Step 4**: Default to English.
- Also detects explicit switch requests ("English please", "Hindi mein boliye").

### `scope_validator.py` — Guardrails
- Maintains compiled regex patterns per scenario.
- Runs on **both** user input and LLM output (double guard).
- Returns redirect responses in the user's current language when a violation is detected.
- Logs every violation for analytics.

### `llm_processor.py` — LLM Orchestration
- Injects language instruction and sentiment context into the system prompt dynamically.
- Calls scope validator before and after the LLM.
- Handles OpenAI errors gracefully with bilingual fallback messages.

### `stt_engine.py` — Speech-to-Text
- Wraps Deepgram's async streaming API.
- Configures multilingual (`"multi"`) mode for English + Hindi.
- Exposes both file transcription (for testing) and streaming (for production).

### `tts_engine.py` — Text-to-Speech
- `ElevenLabsTTSEngine`: Indian English voice with tuned stability/similarity settings.
- `SarvamTTSEngine`: Native Hindi TTS via Sarvam AI REST API (optional, drop-in for Hindi turns).

### `livekit_manager.py` — Room Administration
- Token generation for participants.
- Room listing and deletion via LiveKit server API.
- Used for testing and deployment scripts; not in the hot path.

## Data Flow: Multilingual Processing

```
User Speech (Hindi or English)
    │
    ▼  [Deepgram STT — nova-3, language=multi]
Transcript + detected_language
    │
    ▼  [LanguageDetector.detect()]
Confirmed Language ("en" | "hi")
    │
    ▼  [ConversationManager.update_language()]
Language switch recorded if changed
    │
    ▼  [ScopeValidator.validate_and_redirect() — user input]
Pass (None) or Redirect string
    │
    ├── Redirect → return immediately, log violation
    │
    ▼  [LLMProcessor._build_messages()]
System prompt + language instruction + history
    │
    ▼  [OpenAI GPT-4o]
Raw LLM response
    │
    ▼  [ScopeValidator.validate_and_redirect() — LLM output]
Safe response
    │
    ▼  [ElevenLabs TTS — Indian English voice]
Audio stream → LiveKit → User
```

## Conversation Context Object

```json
{
  "conversation_id": "uuid4",
  "current_language": "en | hi",
  "language_history": ["en", "hi", "en"],
  "user_intent": "schedule_demo",
  "entities_extracted": {
    "company_name": "Acme Corp",
    "company_size": "500 employees",
    "industry": "healthcare"
  },
  "conversation_history": [
    {"role": "user", "content": "...", "language": "en", "timestamp": "..."},
    {"role": "assistant", "content": "...", "language": "en", "timestamp": "..."}
  ],
  "scenario": "presale",
  "conversation_start_time": "ISO8601",
  "turn_count": 6,
  "sentiment": "positive",
  "language_switch_count": 1,
  "scope_violations": 0,
  "topics_discussed": ["product_features", "company_info"]
}
```

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Voice Framework | LiveKit Agents | WebRTC, VAD, audio pipeline |
| STT | Deepgram nova-3 | Multilingual, low latency |
| LLM | OpenAI GPT-4o | Context-aware responses |
| TTS | ElevenLabs Turbo v2.5 | Indian English voice |
| TTS (Hindi alt) | Sarvam AI | Native Hindi, optional |
| Language Detection | Heuristics + langdetect | <100ms |
| Backend | Python 3.11 | Async throughout |
| Config | YAML + .env | Per-scenario overrides |
| Containerisation | Docker | Single-image deployment |
