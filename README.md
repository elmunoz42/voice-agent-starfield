# AstroLB-3 - Starfield Suit AI Voice Companion

A private, in-helmet suit AI for Starfield powered by LiveKit voice agents. AstroLB-3 runs on your phone with earbuds, completely separate from the game. No mods, no game files, no code on your gaming PC required.

Talk to AstroLB-3 hands-free while you play. Ask about Starfield mechanics, get quest guidance, track your progress, and receive spoiler-controlled advice from a curated knowledge base.

## Status

| Milestone | Status | Description |
|-----------|--------|-------------|
| M0 | ✅ Built | Voice loop (console mode, OpenAI STT/LLM/TTS) |
| M1 | ✅ Built | Knowledge base (YouTube ingestion, distillation, RAG with LanceDB) |
| M2 | ✅ Built | Progress journal and spoiler control (SQLite) |
| M3 | ✅ Built | Phone deployment (LiveKit Cloud + Vercel frontend) |
| M4 | ⏳ Planned | Playtest scenarios |

## Project Structure

```
voice-agent-starfield/
├── agent/                      # Python voice agent (uv project)
│   ├── voice_agent.py          # Main agent implementation
│   ├── journal.py              # Progress journal module
│   ├── kb.py                   # Knowledge base CLI
│   ├── tests/                  # Unit tests
│   ├── pyproject.toml          # Dependencies (pinned with uv.lock)
│   ├── .env.example            # Environment template
│   └── .env                    # Secrets (not in git)
├── prompts/
│   └── suit-ai.md              # AstroLB-3 system prompt
├── knowledge-base/             # Curated Starfield guides (versioned)
├── data/                       # Not in git
│   ├── raw/                    # YouTube transcripts
│   ├── journal.db              # Progress tracking (M2)
│   └── lancedb/                # Vector store (M1)
├── frontend/                   # Next.js app (agent-starter-react)
├── docs/
│   ├── setup.md                # Setup instructions
│   ├── kb-guide.md             # Knowledge base pipeline guide
│   └── playtest.md             # Playtest scenarios and results
└── README.md
```

## Features

### Implemented

**M0 - Voice Loop**
- ✅ Voice conversation with OpenAI Whisper (STT), GPT (LLM), and TTS
- ✅ AstroLB-3 personality: calm, brief, dry suit AI
- ✅ Voice-optimized responses (2-3 sentences max, one question at a time)
- ✅ Console mode for local testing with PC microphone
- ✅ Configurable models via environment variables

**M1 - Knowledge Base**
- ✅ `kb add-youtube` - Fetch YouTube video/playlist transcripts
- ✅ `kb add-page` - Fetch web page content for distillation
- ✅ `kb distill` - LLM-powered conversion to structured Markdown guides
- ✅ `kb ingest` - Chunk by heading, embed with OpenAI, store in LanceDB
- ✅ `kb search` - Test retrieval with spoiler filtering
- ✅ Agent `search_knowledge_base` tool with lazy loading
- ✅ Idempotent ingestion with content hashing
- ✅ Embedded LanceDB (portable, no external database needed)

**M2 - Progress Journal**
- ✅ `log_progress` tool - Record accomplishments and discoveries
- ✅ `recall_progress` tool - Retrieve journal entries by topic
- ✅ `set_current_goal` tool - Track active objectives
- ✅ `set_spoiler_level` tool - Control plot information visibility
- ✅ SQLite-based journal (data/journal.db)
- ✅ Session greetings with progress context ("Last time you were...")
- ✅ Spoiler filtering integrated with knowledge base search
- ✅ Four spoiler levels: none, main-quest, faction, endgame
- ✅ Unit tests for journal functions

**M3 - Phone Deployment**
- ✅ Next.js 16 frontend with LiveKit integration
- ✅ Push-to-talk interface (large circular button, touch-optimized)
- ✅ Passphrase-protected access
- ✅ PWA manifest for home screen installation
- ✅ LiveKit Cloud agent deployment support
- ✅ Vercel frontend hosting configuration
- ✅ AstroLB-3 branding with Starfield theme
- ✅ Voice visualizer with agent state indicators
- ✅ Example commands display

### Planned
- ⏳ Playtest scenarios and refinements

## Quick Start

### Prerequisites
- Python 3.11 or later
- OpenAI API key (not ChatGPT subscription - actual API key)
- `uv` package manager

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cd agent
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Build Knowledge Base (Optional)

```bash
# Fetch a YouTube video transcript
uv run python kb.py add-youtube "https://youtube.com/watch?v=VIDEO_ID"

# Distill into markdown guide
uv run python kb.py distill

# Review and edit the generated markdown in knowledge-base/

# Ingest into LanceDB
uv run python kb.py ingest

# Test search
uv run python kb.py search "how do I build a ship"
```

### 4. Run in Console Mode

```bash
uv run python voice_agent.py console
```

Talk to AstroLB-3 through your PC microphone. Say "Astro" to get its attention.
If you built a knowledge base, ask questions about Starfield mechanics.

## Model Configuration

Edit `agent/.env` to customize:

- `LLM_MODEL`: gpt-4o-mini (default), gpt-4o, gpt-4-turbo
- `STT_MODEL`: whisper-1 (OpenAI Whisper)
- `TTS_MODEL`: tts-1 (standard) or tts-1-hd (higher quality)
- `TTS_VOICE`: onyx (recommended), alloy, echo, fable, nova, shimmer

## Knowledge Base CLI

The `kb.py` CLI manages the Starfield knowledge base pipeline:

### Commands

- `kb add-youtube <url>` - Fetch YouTube video or playlist transcripts
- `kb add-page <url>` - Fetch web page content (respecting terms of service)
- `kb distill` - Convert raw transcripts to structured Markdown guides with LLM
- `kb ingest` - Chunk, embed, and store guides in LanceDB
- `kb search "<query>"` - Test retrieval without running voice agent

### Workflow

1. **Collect sources**: Use `add-youtube` or `add-page` to fetch content into `data/raw/`
2. **Distill**: Run `distill` to convert to curated markdown in `knowledge-base/`
3. **Review**: Edit the generated markdown files (they are versioned source of truth)
4. **Ingest**: Run `ingest` to chunk, embed, and store in LanceDB
5. **Test**: Use `search` to verify retrieval quality

The ingestion is idempotent - re-running won't duplicate chunks with unchanged content.

## Phone Deployment (M3)

AstroLB-3 is designed to run on your phone with earbuds while you play Starfield. This keeps the AI companion private and separate from your game.

### Quick Deployment

1. **Deploy agent to LiveKit Cloud**
   ```bash
   cd agent
   lk cloud auth
   lk agent create
   ```

2. **Deploy frontend to Vercel**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Access from phone**
   - Open the Vercel URL on your phone
   - Add to home screen (PWA)
   - Connect earbuds and talk to AstroLB-3

**For detailed step-by-step instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

The deployment guide covers:
- Installing LiveKit CLI
- Setting up LiveKit Cloud credentials
- Deploying the voice agent
- Configuring Vercel with environment variables
- Installing as a PWA on iOS and Android
- Troubleshooting connection and audio issues

## Roadmap

See the status table above for current progress. Only verified items are checked.

Next steps:
1. ✅ ~~Build knowledge base ingestion CLI (M1)~~
2. ✅ ~~Implement progress journal tools (M2)~~
3. ✅ ~~Deploy to phone (M3)~~
4. Run playtest scenarios (M4)

## Why Separate from Game?

- **No mods required**: Avoids AISS license restrictions and game file modifications
- **Always available**: Works whether the game is running or not
- **Privacy**: Only you hear AstroLB-3 (earbuds, not game audio)
- **Portable**: Knowledge base and agent run on phone or cloud

## Documentation

- [Setup Guide](docs/setup.md) - Detailed installation and configuration
- [Playtest Results](docs/playtest.md) - Test scenarios and observations

## License

Private project for Carlos. Not for distribution.
