# Deployment Guide

## Local Development

See [SETUP.md](SETUP.md) for local setup. Once configured:

```bash
cd src && python main.py start
```

---

## Docker (Single Container)

### Build

```bash
docker build -t voicebot-presale:latest .
```

### Run

```bash
docker run -d \
  --name voicebot \
  --env-file .env \
  --restart unless-stopped \
  voicebot-presale:latest
```

### View Logs

```bash
docker logs -f voicebot
```

---

## AWS EC2 Deployment

### 1. Launch an EC2 Instance

- AMI: Ubuntu 22.04 LTS
- Instance type: `t3.medium` (minimum); `t3.large` recommended for production
- Security group: allow outbound HTTPS (443) and WSS (443) for LiveKit

### 2. Install Docker on EC2

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

### 3. Transfer and Run

```bash
# On your local machine
scp -i your-key.pem .env ubuntu@YOUR_EC2_IP:~/voicebot.env

# On EC2
docker pull your-registry/voicebot-presale:latest
docker run -d \
  --name voicebot \
  --env-file ~/voicebot.env \
  --restart always \
  your-registry/voicebot-presale:latest
```

### 4. Set Up CloudWatch Logging (optional)

```bash
docker run -d \
  --name voicebot \
  --env-file ~/voicebot.env \
  --log-driver=awslogs \
  --log-opt awslogs-region=ap-south-1 \
  --log-opt awslogs-group=/voicebot/presale \
  --restart always \
  your-registry/voicebot-presale:latest
```

---

## Google Cloud Run Deployment

### 1. Build and Push to Artifact Registry

```bash
gcloud auth configure-docker asia-south1-docker.pkg.dev

docker build -t asia-south1-docker.pkg.dev/YOUR_PROJECT/voicebot/presale:latest .
docker push asia-south1-docker.pkg.dev/YOUR_PROJECT/voicebot/presale:latest
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy voicebot-presale \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT/voicebot/presale:latest \
  --region asia-south1 \
  --platform managed \
  --set-env-vars LIVEKIT_URL=wss://your.livekit.cloud \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --set-secrets DEEPGRAM_API_KEY=deepgram-key:latest \
  --set-secrets ELEVENLABS_API_KEY=elevenlabs-key:latest \
  --set-secrets LIVEKIT_API_KEY=livekit-api-key:latest \
  --set-secrets LIVEKIT_API_SECRET=livekit-api-secret:latest \
  --min-instances 1 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 1
```

> **Note**: Store secrets in Google Secret Manager rather than plain env vars for production.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `LIVEKIT_URL` | ✅ | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | ✅ | LiveKit API key |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit API secret |
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `OPENAI_MODEL` | ❌ | LLM model (default: `gpt-4o`) |
| `DEEPGRAM_API_KEY` | ✅ | Deepgram API key |
| `ELEVENLABS_API_KEY` | ✅ | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | ❌ | Voice ID (default: Indian English) |
| `SARVAM_API_KEY` | ❌ | Sarvam AI key (Hindi TTS only) |
| `LOG_LEVEL` | ❌ | Logging level (default: `INFO`) |
| `SCENARIO` | ❌ | Bot scenario (default: `presale`) |

---

## Scaling

The LiveKit Agents framework supports horizontal scaling natively:

1. Run multiple worker instances pointing to the same LiveKit Cloud project.
2. LiveKit automatically distributes room assignments across available workers.
3. Each worker can handle multiple concurrent sessions depending on CPU/memory.

For load testing, use [LiveKit's load test tool](https://docs.livekit.io/agents/load-testing/).
