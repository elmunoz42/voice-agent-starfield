# Knowledge Base Guide - AstroLB-3

This guide explains how to build and maintain the Starfield knowledge base for AstroLB-3.

## Overview

The knowledge base pipeline transforms raw video transcripts and web pages into searchable, structured guides:

1. **Fetch** - Download transcripts from YouTube or text from web pages
2. **Distill** - Use LLM to convert into organized Markdown guides
3. **Review** - Manually edit and curate the generated guides
4. **Ingest** - Chunk, embed, and store in LanceDB vector database
5. **Search** - Test retrieval quality

## Prerequisites

- OpenAI API key configured in `agent/.env`
- `uv sync` completed to install dependencies

## Commands

All commands are run from the agent directory:

```bash
cd agent
```

### 1. Fetch YouTube Transcripts

```bash
uv run python kb.py add-youtube "https://www.youtube.com/watch?v=VIDEO_ID"
```

**For playlists:**
```bash
uv run python kb.py add-youtube "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

**What it does:**
- Downloads transcript using youtube-transcript-api
- Falls back to yt-dlp if needed
- Saves to `data/raw/VIDEO_ID.json` (gitignored)

### 2. Fetch Web Pages

```bash
uv run python kb.py add-page "https://example.com/starfield-guide"
```

**What it does:**
- Fetches web page content
- Extracts text (removes scripts, styles)
- Saves to `data/raw/page_HASH.json`
- **Only use for sites that allow scraping**

### 3. Distill Into Markdown

```bash
uv run python kb.py distill
```

**What it does:**
- Finds all JSON files in `data/raw/`
- Calls OpenAI LLM to convert each to structured Markdown
- Organizes by topic headings
- Adds spoiler tags (none, main-quest, faction, endgame)
- Saves to `knowledge-base/VIDEO_ID.md`

**Output format:**
```markdown
---
source: https://youtube.com/watch?v=VIDEO_ID
video_timestamps: [timestamps]
---

<!-- spoiler: none -->
## Ship Building Basics

General ship building mechanics...

<!-- spoiler: main-quest -->
## Constellation Ship Upgrades

Quest-specific ship information...
```

### 4. Review and Edit

**IMPORTANT**: The markdown files in `knowledge-base/` are the versioned source of truth.

- Review each generated file for accuracy
- Edit, reorganize, or combine sections as needed
- Verify spoiler tags are appropriate
- Add citations and timestamps if missing
- Commit edited files to git

**Spoiler tag rules** (enforced by `_chunk_markdown()` in `kb.py`):
- Put `<!-- spoiler: LEVEL -->` on the line directly above each `##` heading.
- An untagged section inherits the closest tag above it, so plot never leaks as `none`.
- Keep each `##` section under ~1,500 characters so it embeds as one chunk; longer sections are packed into several chunks by paragraph.

### 5. Ingest Into LanceDB

```bash
uv run python kb.py ingest
```

**What it does:**
- Reads all `.md` files in `knowledge-base/`
- Chunks by `##` headings (splits large chunks at paragraphs)
- Computes content hash for each chunk
- Generates OpenAI embeddings (`text-embedding-3-small`)
- Stores in LanceDB at `data/lancedb/` (gitignored)

**Idempotency:**
- Re-running won't duplicate unchanged chunks (TODO: implement hash checking)
- Currently overwrites the table on each run
- Safe to run after editing markdown files

### 6. Test Search

```bash
uv run python kb.py search "how do I build an outpost"
```

**Options:**
```bash
# Limit results
uv run python kb.py search "ship weapons" --limit 5

# Filter by spoiler level
uv run python kb.py search "final mission" --spoiler-level endgame
```

**Spoiler levels:**
- `none` - General mechanics, no plot
- `main-quest` - Constellation storyline allowed
- `faction` - Faction quests allowed
- `endgame` - Full spoilers including Starborn/Unity

## Building Your First Knowledge Base

### Example: Ship Building Guide

```bash
# 1. Find a good Starfield ship building video
uv run python kb.py add-youtube "https://www.youtube.com/watch?v=EXAMPLE"

# 2. Distill it
uv run python kb.py distill

# 3. Review the generated markdown
nano ../knowledge-base/EXAMPLE.md

# 4. Ingest
uv run python kb.py ingest

# 5. Test
uv run python kb.py search "best ship weapons"
```

### Seed Topics Recommended

Start with ~10 core topics:
- Ship building and customization
- Outpost construction and resource extraction
- Skills and character builds
- Credits and economy
- Combat mechanics
- Main quest overview (spoiler-tagged)
- Faction quests (spoiler-tagged)
- Starborn powers (endgame spoiler)
- Settled Systems and locations
- Resources and crafting

## Maintenance

### Adding New Content

1. Fetch new source with `add-youtube` or `add-page`
2. Run `distill`
3. Review and edit the new markdown file
4. Run `ingest` to update the vector store
5. Test with `search`

### Updating Existing Guides

1. Edit the markdown file in `knowledge-base/`
2. Run `ingest` to re-embed
3. Commit the edited markdown to git

### Checking Ingestion Status

```bash
# Count chunks in database
cd agent
uv run python -c "import lancedb; db = lancedb.connect('../data/lancedb'); print(db.open_table('starfield_kb').count_rows())"
```

## Troubleshooting

### "No transcript available"
- Video may not have captions
- Try a different video
- yt-dlp fallback is not fully implemented yet

### "No results found in knowledge base"
- Run `kb ingest` to populate the database
- Check that markdown files exist in `knowledge-base/`
- Verify OpenAI API key is set

### LLM distillation produces poor quality
- Edit the markdown manually
- Adjust the system prompt in `kb.py` `_distill_with_llm()`
- Try a better model (gpt-4o instead of gpt-4o-mini)

### Search returns irrelevant results
- Improve the markdown content (better headings, clearer text)
- Adjust chunk sizes in `kb.py` `_chunk_markdown()`
- Increase search limit and review top results

## Best Practices

1. **Curate, don't just ingest** - Always review and edit LLM output
2. **Keep sources** - Maintain source URLs and timestamps
3. **Tag spoilers accurately** - Use the finest granularity needed
4. **Test retrieval** - Use `kb search` after each ingest
5. **Commit markdown** - Knowledge base files are source of truth, commit them
6. **Don't commit data/** - Raw transcripts and vectors stay local
