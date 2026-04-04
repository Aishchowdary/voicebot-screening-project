# Setup Guide

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or 3.11 | 3.11 recommended |
| pip | latest | `pip install --upgrade pip` |
| Git | any | for cloning the repo |
| Docker | 24+ | optional, for containerised runs |

You will also need accounts and API keys for:

- **LiveKit Cloud** — [livekit.io](https://livekit.io) (free tier available)
- **Deepgram** — [deepgram.com](https://deepgram.com) (free $200 credit on signup)
- **OpenAI** — [platform.openai.com](https://platform.openai.com)
- **ElevenLabs** — [elevenlabs.io](https://elevenlabs.io) (free tier available)
- **Sarvam AI** *(optional, for native Hindi TTS)* — [sarvam.ai](https://sarvam.ai)

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/voicebot-screening-project.git
cd voicebot-screening-project
```

## 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in your credentials:

```dotenv
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

OPENAI_API_KEY=sk-your_openai_key
OPENAI_MODEL=gpt-4o

DEEPGRAM_API_KEY=your_deepgram_key

ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ   # Indian English voice

# Optional
SARVAM_API_KEY=your_sarvam_key
```

### Finding an Indian English ElevenLabs Voice

1. Log in to [elevenlabs.io](https://elevenlabs.io).
2. Go to **Voice Library** and search for "Indian English".
3. Copy the **Voice ID** from the voice card.
4. Paste it into `ELEVENLABS_VOICE_ID` in your `.env`.

---

## 5. Run the Agent

```bash
cd src
python main.py start
```

The agent will register with LiveKit and wait for a room to be assigned. You should see:

```
2025-01-01 12:00:00 | INFO | livekit.agents | Worker registered successfully
2025-01-01 12:00:00 | INFO | __main__ | Presale voicebot session started
```

## 6. Connect a Client

To test, open a LiveKit room using the [LiveKit Playground](https://playground.livekit.io/) or a custom frontend:

1. Generate a participant token using `src/livekit_manager.py` or the LiveKit dashboard.
2. Join the room — the agent will greet you automatically.

---

## 7. Run Tests

```bash
cd voicebot-screening-project
pytest tests/ -v
```

Expected output:
```
tests/test_language_switching.py::TestDevanagariDetection::test_pure_devanagari PASSED
tests/test_scope_validation.py::TestPresaleScopeValidator::test_out_of_scope_price PASSED
...
```

---

## 8. (Optional) Run with Docker

```bash
# Build the image
docker build -t voicebot-presale .

# Run with your .env file
docker run --env-file .env voicebot-presale
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `LIVEKIT_API_KEY not set` | Check `.env` is in the project root and loaded |
| `ModuleNotFoundError: livekit` | Run `pip install -r requirements.txt` in your venv |
| Agent connects but no audio | Check microphone permissions in the browser/client |
| Hindi not detected | Ensure Deepgram `language=multi` is set; check STT logs |
| ElevenLabs voice sounds wrong | Replace `ELEVENLABS_VOICE_ID` with an Indian English voice ID |

For further help see `docs/TROUBLESHOOTING.md`.
