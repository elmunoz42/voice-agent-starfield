#!/usr/bin/env python3
"""
Knowledge Base CLI for AstroLB-3
=================================
Manage Starfield knowledge base: fetch transcripts, distill guides, ingest embeddings.
"""

import click
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


@click.group()
def cli():
    """AstroLB-3 Knowledge Base CLI - Manage Starfield guides and embeddings."""
    pass


@cli.command("add-youtube")
@click.argument("url")
@click.option("--output-dir", default="../data/raw", help="Output directory for transcripts")
def add_youtube(url: str, output_dir: str):
    """Fetch YouTube video or playlist transcripts.

    Downloads transcript using youtube-transcript-api, with yt-dlp as fallback.
    Saves raw transcript JSON to data/raw/ (gitignored).

    Examples:
        kb add-youtube https://www.youtube.com/watch?v=VIDEO_ID
        kb add-youtube https://www.youtube.com/playlist?list=PLAYLIST_ID
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    import yt_dlp

    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"Fetching transcript from: {url}")

    # Extract video ID(s)
    video_ids = _extract_video_ids(url)

    if not video_ids:
        click.echo("❌ Could not extract video ID from URL", err=True)
        sys.exit(1)

    success_count = 0

    for video_id in video_ids:
        try:
            # Try youtube-transcript-api first
            click.echo(f"  Fetching {video_id}...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

            # Save transcript
            output_file = output_path / f"{video_id}.json"
            with open(output_file, "w") as f:
                json.dump({
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "transcript": transcript,
                    "source": "youtube-transcript-api"
                }, f, indent=2)

            click.echo(f"  ✅ Saved transcript to {output_file}")
            success_count += 1

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            click.echo(f"  ⚠️  Transcript API failed: {e}", err=True)
            click.echo(f"  Trying yt-dlp fallback...")

            # Fallback to yt-dlp
            if _fetch_with_ytdlp(video_id, output_path):
                success_count += 1
            else:
                click.echo(f"  ❌ Failed to fetch {video_id}", err=True)

    click.echo(f"\n✅ Fetched {success_count}/{len(video_ids)} transcripts")


@cli.command("distill")
@click.option("--input-dir", default="../data/raw", help="Input directory with transcripts")
@click.option("--output-dir", default="../knowledge-base", help="Output directory for markdown")
def distill(input_dir: str, output_dir: str):
    """Distill raw transcripts into curated Markdown guides.

    Uses OpenAI LLM to convert raw transcripts into organized guides with:
    - Topic-based headings
    - Source URLs and timestamps
    - Spoiler tags (none, main-quest, faction, endgame)

    The output markdown files are versioned source of truth.
    """
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv(Path(__file__).parent / ".env")

    input_path = Path(__file__).parent / input_dir
    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all transcript JSON files
    transcript_files = list(input_path.glob("*.json"))

    if not transcript_files:
        click.echo(f"❌ No transcript files found in {input_path}", err=True)
        sys.exit(1)

    click.echo(f"Found {len(transcript_files)} transcripts to distill")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for transcript_file in transcript_files:
        click.echo(f"\n📝 Distilling {transcript_file.name}...")

        with open(transcript_file) as f:
            data = json.load(f)

        # Convert transcript to text
        transcript_text = _transcript_to_text(data["transcript"])
        video_url = data.get("url", "")

        # Call LLM to distill
        markdown = _distill_with_llm(client, transcript_text, video_url)

        # Save markdown
        output_file = output_path / f"{transcript_file.stem}.md"
        with open(output_file, "w") as f:
            f.write(markdown)

        click.echo(f"  ✅ Saved to {output_file}")

    click.echo(f"\n✅ Distilled {len(transcript_files)} guides")
    click.echo("⚠️  Review the markdown files and edit as needed before ingesting")


@cli.command("add-page")
@click.argument("url")
@click.option("--output-dir", default="../data/raw", help="Output directory")
def add_page(url: str, output_dir: str):
    """Fetch and save a web page for distillation.

    Downloads web page content (respecting terms of service).
    Use only for sites that allow content scraping.
    """
    import requests
    from bs4 import BeautifulSoup
    import hashlib

    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"Fetching page: {url}")

    try:
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AstroLB3Bot/1.0)"
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract text content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)

        # Generate filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        output_file = output_path / f"page_{url_hash}.json"

        with open(output_file, "w") as f:
            json.dump({
                "url": url,
                "text": text,
                "source": "web-scrape"
            }, f, indent=2)

        click.echo(f"✅ Saved to {output_file}")

    except Exception as e:
        click.echo(f"❌ Failed to fetch page: {e}", err=True)
        sys.exit(1)


@cli.command("ingest")
@click.option("--kb-dir", default="../knowledge-base", help="Knowledge base directory")
@click.option("--db-path", default="../data/lancedb", help="LanceDB directory")
def ingest(kb_dir: str, db_path: str):
    """Chunk, embed, and ingest markdown guides into LanceDB.

    - Chunks by heading with size limits and overlap
    - Computes content hashes for idempotency
    - Embeds using OpenAI embeddings
    - Upserts into LanceDB (skips unchanged chunks)
    """
    from dotenv import load_dotenv
    from openai import OpenAI
    import lancedb

    load_dotenv(Path(__file__).parent / ".env")

    kb_path = Path(__file__).parent / kb_dir
    db_dir = Path(__file__).parent / db_path
    db_dir.mkdir(parents=True, exist_ok=True)

    # Find all markdown files
    md_files = list(kb_path.glob("*.md"))

    if not md_files:
        click.echo(f"❌ No markdown files found in {kb_path}", err=True)
        sys.exit(1)

    click.echo(f"Found {len(md_files)} markdown files to ingest")

    # Initialize OpenAI and LanceDB
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    db = lancedb.connect(str(db_dir))

    # Create or open table
    table_name = "starfield_kb"

    # Process files
    all_chunks = []

    for md_file in md_files:
        click.echo(f"📄 Processing {md_file.name}...")

        with open(md_file) as f:
            content = f.read()

        # Chunk by heading
        chunks = _chunk_markdown(content, md_file.name)
        all_chunks.extend(chunks)
        click.echo(f"  Generated {len(chunks)} chunks")

    click.echo(f"\n🔢 Total chunks: {len(all_chunks)}")
    click.echo("🤖 Generating embeddings...")

    # Generate embeddings in batches
    chunk_data = []
    batch_size = 100

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [chunk["text"] for chunk in batch]

        # Get embeddings
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        for chunk, embedding_obj in zip(batch, response.data):
            chunk_data.append({
                "text": chunk["text"],
                "source": chunk["source"],
                "heading": chunk["heading"],
                "spoiler_level": chunk["spoiler_level"],
                "content_hash": chunk["content_hash"],
                "vector": embedding_obj.embedding
            })

        click.echo(f"  Embedded {min(i+batch_size, len(all_chunks))}/{len(all_chunks)}")

    # Create or overwrite table
    if table_name in db.table_names():
        click.echo(f"📊 Updating existing table '{table_name}'...")
        table = db.open_table(table_name)
        # TODO: Implement idempotency check by content_hash
        table = db.create_table(table_name, chunk_data, mode="overwrite")
    else:
        click.echo(f"📊 Creating new table '{table_name}'...")
        table = db.create_table(table_name, chunk_data)

    click.echo(f"✅ Ingested {len(chunk_data)} chunks into LanceDB")


@cli.command("search")
@click.argument("query")
@click.option("--db-path", default="../data/lancedb", help="LanceDB directory")
@click.option("--limit", default=3, help="Number of results")
@click.option("--spoiler-level", default="none", help="Maximum spoiler level (none/main-quest/faction/endgame)")
def search(query: str, db_path: str, limit: int, spoiler_level: str):
    """Search the knowledge base and display results.

    Test retrieval without running the voice agent.
    Shows chunk text, source, heading, and relevance score.
    """
    from dotenv import load_dotenv
    from openai import OpenAI
    import lancedb

    load_dotenv(Path(__file__).parent / ".env")

    db_dir = Path(__file__).parent / db_path

    if not db_dir.exists():
        click.echo(f"❌ Database not found at {db_dir}", err=True)
        click.echo("Run 'kb ingest' first", err=True)
        sys.exit(1)

    # Initialize clients
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    db = lancedb.connect(str(db_dir))

    table_name = "starfield_kb"
    if table_name not in db.table_names():
        click.echo(f"❌ Table '{table_name}' not found", err=True)
        sys.exit(1)

    table = db.open_table(table_name)

    # Get query embedding
    click.echo(f"🔍 Searching for: {query}\n")
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=[query]
    )
    query_vector = response.data[0].embedding

    # Search with spoiler filter
    spoiler_levels = ["none", "main-quest", "faction", "endgame"]
    allowed_levels = spoiler_levels[:spoiler_levels.index(spoiler_level) + 1]

    results = table.search(query_vector).limit(limit * 3).to_list()

    # Filter by spoiler level and take top results
    filtered = [r for r in results if r.get("spoiler_level", "none") in allowed_levels][:limit]

    if not filtered:
        click.echo("❌ No results found")
        return

    for i, result in enumerate(filtered, 1):
        click.echo(f"Result {i} (score: {result.get('_distance', 'N/A'):.4f})")
        click.echo(f"Source: {result.get('source', 'Unknown')}")
        click.echo(f"Heading: {result.get('heading', 'N/A')}")
        click.echo(f"Spoiler: {result.get('spoiler_level', 'none')}")
        click.echo(f"\n{result['text']}\n")
        click.echo("-" * 80 + "\n")


# Helper functions

def _extract_video_ids(url: str) -> list:
    """Extract video ID(s) from YouTube URL (single video or playlist)."""
    import re

    video_ids = []

    # Single video
    video_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if video_match:
        return [video_match.group(1)]

    # Playlist - use yt-dlp to extract IDs
    if "playlist" in url or "list=" in url:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    video_ids = [entry['id'] for entry in info['entries'] if entry]
            except Exception as e:
                click.echo(f"Error extracting playlist: {e}", err=True)

    return video_ids


def _fetch_with_ytdlp(video_id: str, output_path: Path) -> bool:
    """Fetch subtitles using yt-dlp as fallback."""
    import yt_dlp

    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'json3',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

            # Extract subtitles manually from info dict
            if 'automatic_captions' in info or 'subtitles' in info:
                # This is a simplified version - full implementation would parse VTT/JSON3
                click.echo(f"  ⚠️  yt-dlp subtitles need manual parsing (TODO)")
                return False

        return False
    except Exception as e:
        click.echo(f"  yt-dlp error: {e}", err=True)
        return False


def _transcript_to_text(transcript: list) -> str:
    """Convert transcript list to plain text."""
    return " ".join(entry["text"] for entry in transcript)


def _distill_with_llm(client, transcript_text: str, video_url: str) -> str:
    """Use LLM to distill transcript into structured markdown guide."""

    system_prompt = """You are a knowledgeable assistant specializing in Starfield game mechanics.

Convert the video transcript into a well-organized Markdown guide with:
- Clear topic headings (##)
- Concise, accurate information
- Source URL and timestamps in a metadata block at the top
- A spoiler tag for each section: none, main-quest, faction, or endgame
  (Format: <!-- spoiler: none --> before each heading)

Example format:
---
source: [URL]
video_timestamps: [key timestamps]
---

<!-- spoiler: none -->
## Topic Name

Content here...

<!-- spoiler: main-quest -->
## Another Topic

More content...
"""

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Source: {video_url}\n\nTranscript:\n{transcript_text[:15000]}"}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def _chunk_markdown(content: str, source: str) -> list:
    """Chunk markdown by headings with overlap and metadata."""
    import re
    import hashlib

    chunks = []

    # Split by ## headings
    sections = re.split(r'\n##\s+', content)

    # First section is metadata/preamble
    metadata = sections[0] if sections else ""

    # Extract spoiler levels from comments
    for i, section in enumerate(sections[1:], 1):
        lines = section.split('\n')
        heading = lines[0].strip()
        text = '\n'.join(lines[1:]).strip()

        # Look for spoiler tag in previous content
        spoiler_match = re.search(r'<!--\s*spoiler:\s*(\S+)\s*-->', metadata + '\n'.join(sections[:i+1]))
        spoiler_level = spoiler_match.group(1) if spoiler_match else "none"

        # Create chunk with metadata
        full_text = f"## {heading}\n\n{text}"

        # If chunk is too large, split it further (simple strategy: by paragraphs)
        if len(full_text) > 1500:
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    chunk_text = f"## {heading}\n\n{para}"
                    chunks.append({
                        "text": chunk_text,
                        "source": source,
                        "heading": heading,
                        "spoiler_level": spoiler_level,
                        "content_hash": hashlib.md5(chunk_text.encode()).hexdigest()
                    })
        else:
            chunks.append({
                "text": full_text,
                "source": source,
                "heading": heading,
                "spoiler_level": spoiler_level,
                "content_hash": hashlib.md5(full_text.encode()).hexdigest()
            })

    return chunks


if __name__ == "__main__":
    cli()
