# Setup Guide - AstroLB-3 Starfield Voice Agent

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.11 or later**
   ```bash
   python --version
   ```

2. **uv package manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **OpenAI API Key**
   - Get yours at https://platform.openai.com/api-keys
   - Note: ChatGPT subscription tokens do NOT work for API calls
   - You need an actual OpenAI API key with credits

4. **(Optional) LiveKit Cloud account** - Only needed for phone deployment (M3)
   - Free tier available at https://cloud.livekit.io

## Installation

### 1. Clone and Enter Directory

```bash
cd /home/elmunoz42/cmkdev/voice-agent-starfield
```

### 2. Install Agent Dependencies

```bash
uv sync
```

This creates a virtual environment at `.venv/` and installs all dependencies with pinned versions from `uv.lock`.

### 3. Configure Environment Variables

```bash
cd agent
cp .env.example .env
```

Edit `agent/.env` and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. Verify Installation

```bash
uv run python agent/voice_agent.py --help
```

You should see LiveKit agent CLI help output.

## Running the Agent

### Console Mode (Local Testing)

Console mode uses your PC microphone and speakers. Best for initial testing.

```bash
uv run python agent/voice_agent.py console
```

- Speak into your microphone
- AstroLB-3 will respond through your speakers
- Press Ctrl+C to exit

### Dev Mode (Browser-Based)

Dev mode opens a web interface at `http://localhost:3000`.

```bash
uv run python agent/voice_agent.py dev
```

- Browser opens automatically
- Click "Connect" to start voice session
- Uses browser's microphone/speakers

### Start Mode (Production Worker)

Start mode connects to LiveKit Cloud or your LiveKit server. Used for phone deployment.

```bash
uv run python agent/voice_agent.py start
```

Requires LiveKit credentials in `.env`:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

## Model Configuration

Edit `agent/.env` to customize voice pipeline models:

### LLM (Large Language Model)
```bash
LLM_MODEL=gpt-4o-mini  # Default, fast and cheap
# Alternatives: gpt-4o, gpt-4-turbo
```

### STT (Speech-to-Text)
```bash
STT_MODEL=whisper-1  # OpenAI Whisper
```

### TTS (Text-to-Speech)
```bash
TTS_MODEL=tts-1       # Standard quality
# Alternative: tts-1-hd (higher quality, slower)

TTS_VOICE=onyx        # Deep, calm, professional (recommended for AstroLB-3)
# Alternatives: alloy, echo, fable, nova, shimmer
```

## Troubleshooting

### "No module named 'livekit'"
Run `uv sync` to install dependencies.

### "OpenAI API key not found"
Ensure `OPENAI_API_KEY` is set in `agent/.env`.

### Microphone not detected (console mode)
Check your system's default audio input device. LiveKit uses the OS default.

### High latency in responses
- Try `TTS_MODEL=tts-1` instead of `tts-1-hd`
- Check your internet connection
- Consider using `gpt-4o-mini` instead of `gpt-4o`

## Next Steps

Once the basic voice loop works:
1. Build the knowledge base (M1) - see knowledge base CLI docs
2. Add progress tracking (M2) - journal tools
3. Deploy to phone (M3) - LiveKit Cloud + Vercel frontend

## References

- LiveKit Agents documentation: https://docs.livekit.io/agents/
- OpenAI API documentation: https://platform.openai.com/docs/
- uv documentation: https://github.com/astral-sh/uv
