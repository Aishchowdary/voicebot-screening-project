# ============================================================
# Dockerfile — AI Presale Voicebot (LiveKit Agent)
# ============================================================
FROM python:3.11-slim

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Working directory ---
WORKDIR /app

# --- Python dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Application code ---
COPY src/ ./src/
COPY config/ ./config/

# --- Logs directory ---
RUN mkdir -p logs

# --- Non-root user for security ---
RUN useradd --create-home --shell /bin/bash voicebot && \
    chown -R voicebot:voicebot /app
USER voicebot

# --- Entrypoint ---
# The LiveKit agent CLI handles worker lifecycle.
WORKDIR /app/src
CMD ["python", "main.py", "start"]

# Health-check via LiveKit agent default HTTP port
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
