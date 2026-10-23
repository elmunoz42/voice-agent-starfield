# AstroLB-3 - Starfield Suit AI Voice Companion

A private, in-helmet suit AI for Starfield powered by LiveKit voice agents. AstroLB-3 runs on your phone with earbuds, completely separate from the game. No mods, no game files, no code on your gaming PC required.

Talk to AstroLB-3 hands-free while you play. Ask about Starfield mechanics, get quest guidance, track your progress, and receive spoiler-controlled advice from a curated knowledge base.

## Status

| Milestone | Status | Description |
|-----------|--------|-------------|
| M0 | ✅ Built | Voice loop (console mode, OpenAI STT/LLM/TTS) |
| M1 | ✅ Built | Knowledge base (YouTube ingestion, distillation, RAG with LanceDB) |
| M2 | ⏳ Planned | Progress journal and spoiler control (SQLite) |
| M3 | ⏳ Planned | Phone deployment (LiveKit Cloud + Vercel frontend) |
| M4 | ⏳ Planned | Playtest scenarios |

## Project Structure

```
voice-agent-starfield/
├── agent/                      # Python voice agent (uv project)
│   ├── voice_agent.py          # Main agent implementation
│   ├── kb.py                   # Knowledge base CLI
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

### Planned
- ⏳ Progress journal with SQLite (goals, notes, timestamps)
- ⏳ Full spoiler-level filtering integrated with progress tracking
- ⏳ Phone-optimized frontend with push-to-talk
- ⏳ LiveKit Cloud deployment

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

## Roadmap

See the status table above for current progress. Only verified items are checked.

Next steps:
1. ✅ ~~Build knowledge base ingestion CLI (M1)~~
2. Implement progress journal tools (M2)
3. Deploy to phone (M3)
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
