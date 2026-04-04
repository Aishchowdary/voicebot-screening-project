# 🎙️ AI Presale Voicebot — LiveKit Multilingual Voice Agent

A production-grade, **bilingual (English + Hindi)** AI presale voicebot built on the **LiveKit Agents** framework. The bot conducts natural presale conversations with an **Indian English accent**, seamlessly switches between languages, and strictly enforces presale scope boundaries.

---

## ✨ Features

| Feature | Status |
|---|---|
| Real-time voice pipeline (LiveKit + WebRTC) | ✅ |
| Multilingual STT — English & Hindi (Deepgram nova-3) | ✅ |
| GPT-4o LLM with multi-turn context | ✅ |
| Indian English TTS (ElevenLabs Turbo) | ✅ |
| Native Hindi TTS alternative (Sarvam AI) | ✅ optional |
| Automatic language detection | ✅ |
| Explicit language switching ("English please" / "Hindi mein boliye") | ✅ |
| Context preservation across language switches | ✅ |
| Strict presale scope enforcement (double guard) | ✅ |
| Graceful out-of-scope redirection in both languages | ✅ |
| Conversation logging with full audit trail | ✅ |
| Sentiment tracking | ✅ |
| Docker containerisation | ✅ |
| Full test suite (pytest) | ✅ |

---

## 🏗️ Architecture

```
User Speech → LiveKit → Deepgram STT → Language Detector
    → Scope Validator (input) → GPT-4o LLM
    → Scope Validator (output) → ElevenLabs TTS → User
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full architecture diagram and component descriptions.

---

## 📁 Project Structure

```
voicebot-screening-project/
├── src/
│   ├── main.py                  # LiveKit agent entry point
│   ├── livekit_manager.py       # Room management & token generation
│   ├── stt_engine.py            # Deepgram STT wrapper
│   ├── llm_processor.py         # LLM orchestration with context & scope
│   ├── tts_engine.py            # ElevenLabs + Sarvam TTS engines
│   ├── language_detector.py     # Heuristic + library language detection
│   ├── conversation_manager.py  # Session state & conversation history
│   └── scope_validator.py       # Presale scope enforcement & redirection
├── config/
│   ├── scenarios/
│   │   └── presale_config.yaml  # Full scenario configuration
│   ├── prompts/
│   │   └── presale_system_prompt.txt
│   └── settings.py              # Centralised settings loader
├── tests/
│   ├── test_stt.py
│   ├── test_llm.py
│   ├── test_language_switching.py
│   └── test_scope_validation.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── logs/                        # Conversation logs (gitignored)
├── .env.example                 # Environment variable template
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/voicebot-screening-project.git
cd voicebot-screening-project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required credentials:
- **LiveKit** — [livekit.io](https://livekit.io)
- **Deepgram** — [deepgram.com](https://deepgram.com)
- **OpenAI** — [platform.openai.com](https://platform.openai.com)
- **ElevenLabs** — [elevenlabs.io](https://elevenlabs.io)

### 3. Run

```bash
cd src
python main.py start
```

### 4. Test

```bash
pytest tests/ -v
```

For full setup details see [`docs/SETUP.md`](docs/SETUP.md).

---

## 💬 Sample Conversations

### English Presale Conversation

```
Bot:  "Namaste! Hello! Welcome. I'm Priya, your presale assistant.
       You can speak with me in English or Hindi. What brings you here today?"

User: "Hi, I'm looking for a solution to automate my customer calls."

Bot:  "That's a great use case! We specialise in exactly that. Could you tell
       me a bit about your business and how many calls you handle daily?"

User: "We get about 500 calls a day for appointment scheduling."

Bot:  "500 daily calls for scheduling is a perfect fit for automation.
       Our platform handles booking, rescheduling, and cancellations seamlessly.
       Are you currently using any calendar system like Google Calendar?"
```

### Hindi ↔ English Language Switch

```
User: "Namaste, main aapke product ke baare mein jaanna chahta hoon."

Bot:  "Namaste! Mujhe khushi hai ki aap hamare baare mein jaanna chahte hain.
       Aap English mein baat karna pasand karenge ya Hindi mein?"

User: "English please."

Bot:  "Of course! Happy to switch to English. So what specific challenges
       are you facing with your current customer communication?"
```

### Out-of-Scope Handling

```
User: "How much does your solution cost?"

Bot:  "That's a great question! Pricing details are best discussed directly
       with our sales team who can tailor a proposal to your specific needs.
       I'd love to schedule that call for you — shall I do that?"

User: "Can I get a 50% discount?"

Bot:  "I appreciate the question! Discount discussions are best handled by
       our sales team. Shall I arrange a meeting with them for you?"
```

---

## 🧪 Test Coverage

| Test File | What it Tests |
|---|---|
| `test_stt.py` | STTResult data class, engine initialisation |
| `test_llm.py` | Scope redirect (no LLM call), in-scope LLM call, fallback responses |
| `test_language_switching.py` | Devanagari detection, Hinglish scoring, explicit switch requests, ConversationManager tracking |
| `test_scope_validation.py` | 15+ in/out-of-scope cases across all three scenarios |

---

## ⚙️ Configuration

All scenario settings are in `config/scenarios/presale_config.yaml`:

```yaml
scenario: presale
languages:
  primary: en
  secondary: hi
  auto_detect: true
tts:
  provider: elevenlabs
  model_id: eleven_turbo_v2_5
llm:
  model: gpt-4o
  temperature: 0.7
  max_tokens: 300
```

---

## 📊 Performance Targets

| Metric | Target | Acceptable |
|---|---|---|
| End-to-end latency | < 1.5s | < 2.5s |
| STT latency | < 500ms | < 800ms |
| LLM response | < 800ms | < 1.2s |
| TTS synthesis | < 300ms | < 500ms |
| Language detection | < 100ms | < 200ms |
| Speech recognition accuracy | > 92% (EN) / > 85% (HI) | — |
| Scope compliance | 100% | — |

---

## 🐳 Docker

```bash
docker build -t voicebot-presale .
docker run --env-file .env voicebot-presale
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for AWS and GCP deployment guides.

---

## 📚 Resources

- [LiveKit Agents Docs](https://docs.livekit.io/agents/)
- [Deepgram STT Docs](https://developers.deepgram.com/)
- [ElevenLabs TTS Docs](https://elevenlabs.io/docs)
- [Sarvam AI (Indian Languages)](https://docs.sarvam.ai/)
- [OpenAI API Docs](https://platform.openai.com/docs/)

---

## 📄 License

MIT License — see `LICENSE` for details.
