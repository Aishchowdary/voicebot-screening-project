# Troubleshooting Guide

## Agent Won't Start

**Symptom**: `python main.py start` exits immediately or throws an error.

**Checks**:
1. Confirm `.env` exists and is populated: `cat .env`
2. Confirm virtual environment is active: `which python` should point inside `.venv/`
3. Confirm all packages are installed: `pip list | grep livekit`
4. Check for missing env vars:
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('LIVEKIT_API_KEY'))"
   ```

---

## Agent Connects but No Audio Heard

**Possible causes**:
- ElevenLabs voice ID is invalid → check `ELEVENLABS_VOICE_ID` in `.env`
- TTS API key has no credits → log in to ElevenLabs dashboard
- LiveKit room is not publishing audio back → check browser microphone permissions

**Debug steps**:
```bash
# Test TTS in isolation
cd src
python - <<'EOF'
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from tts_engine import ElevenLabsTTSEngine

async def test():
    engine = ElevenLabsTTSEngine()
    result = await engine.synthesise("Hello, this is a test.", "en")
    with open("/tmp/test_tts.mp3", "wb") as f:
        f.write(result.audio_bytes)
    print(f"Audio saved: {result.size_kb}KB")

asyncio.run(test())
EOF
```
Then play `/tmp/test_tts.mp3` to verify.

---

## Hindi Not Being Detected

**Symptom**: Agent responds in English even when user speaks Hindi.

**Checks**:
1. Confirm Deepgram is using `language="multi"` — see `stt_engine.py`.
2. Test the language detector directly:
   ```bash
   cd src
   python -c "
   from language_detector import LanguageDetector
   d = LanguageDetector()
   print(d.detect('Namaste main aapke product ke baare mein jaanna chahta hoon'))
   print(d.detect('नमस्ते'))
   "
   ```
3. Ensure `langdetect` is installed: `pip install langdetect`

---

## Scope Violations Appearing Incorrectly

**Symptom**: In-scope queries are being redirected.

**Debug**:
```bash
cd src
python -c "
from scope_validator import ScopeValidator
sv = ScopeValidator('presale')
tests = [
    'What features does your product have?',
    'Can you tell me about integrations?',
    'What are the payment terms?',  # should be out of scope
]
for t in tests:
    print(f'IN SCOPE: {sv.is_in_scope(t)} | {t}')
"
```

If a legitimate query is being blocked, check the regex patterns in `scope_validator.py` and adjust as needed.

---

## High Latency

**Symptom**: End-to-end response time > 2.5 seconds.

**Steps**:
1. Check which component is slow by adding timing logs to `llm_processor.py`.
2. For LLM latency: try `gpt-4o-mini` (`OPENAI_MODEL=gpt-4o-mini`) for faster responses.
3. For TTS latency: ensure `eleven_turbo_v2_5` model is selected (not `eleven_multilingual_v2`).
4. For STT latency: Deepgram nova-3 is already the lowest-latency option.
5. Deploy the agent closer to the LiveKit region (e.g. `ap-south-1` for India).

---

## Tests Failing

```bash
# Run with verbose output
pytest tests/ -v --tb=short

# Run a single test file
pytest tests/test_scope_validation.py -v

# Run with logging
pytest tests/ -v -s --log-cli-level=DEBUG
```

Common fix: ensure `sys.path` in each test file points to `src/`:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
```

---

## Docker Container Crashes

```bash
# Check exit code and logs
docker ps -a
docker logs voicebot --tail 50

# Run interactively to debug
docker run -it --env-file .env voicebot-presale:latest /bin/bash
```

---

## Getting More Help

- [LiveKit Community Slack](https://livekit.io/slack)
- [Deepgram Discord](https://discord.gg/deepgram)
- [ElevenLabs Discord](https://discord.gg/elevenlabs)
- Open a GitHub issue on this repository
