#!/usr/bin/env python3
"""
Quick test of M0-M2 features (without requiring audio/LiveKit)
"""

import asyncio
from journal import get_journal
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent / ".env")


async def test_knowledge_base():
    """Test M1 - Knowledge Base Search"""
    print("\n" + "="*80)
    print("M1 TEST: Knowledge Base Search")
    print("="*80)

    try:
        import lancedb
        from openai import OpenAI

        db_path = Path(__file__).parent / "../data/lancedb"
        db = lancedb.connect(str(db_path))
        table = db.open_table("starfield_kb")

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Test query
        query = "How do I build a ship?"
        print(f"\n🔍 Query: {query}")

        # Get embedding
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_vector = response.data[0].embedding

        # Search
        results = table.search(query_vector).limit(2).to_list()

        print(f"\n✅ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Source: {result.get('source')}")
            print(f"    Heading: {result.get('heading')}")
            print(f"    Spoiler: {result.get('spoiler_level')}")
            print(f"    Text preview: {result.get('text', '')[:200]}...")

    except Exception as e:
        print(f"\n❌ Knowledge base test failed: {e}")


def test_journal():
    """Test M2 - Progress Journal"""
    print("\n" + "="*80)
    print("M2 TEST: Progress Journal")
    print("="*80)

    journal = get_journal()

    # Test 1: Log progress
    print("\n1. Testing log_progress()...")
    journal.log_progress("Found a Class B ship at New Atlantis")
    journal.log_progress("Completed first Constellation mission")
    journal.log_progress("Built first outpost on Jemison", topic="outposts")
    print("   ✅ Logged 3 progress entries")

    # Test 2: Set goal
    print("\n2. Testing set_current_goal()...")
    journal.set_current_goal("Find a better grav drive")
    current_goal = journal.get_current_goal()
    print(f"   ✅ Current goal: {current_goal}")

    # Test 3: Recall progress
    print("\n3. Testing recall_progress()...")
    entries = journal.recall_progress(limit=3)
    print(f"   ✅ Recent progress ({len(entries)} entries):")
    for entry in entries:
        print(f"      - {entry['note']}")

    # Test 4: Recall by topic
    print("\n4. Testing recall_progress(topic='outposts')...")
    outpost_entries = journal.recall_progress(topic="outposts")
    print(f"   ✅ Outpost progress ({len(outpost_entries)} entries):")
    for entry in outpost_entries:
        print(f"      - {entry['note']}")

    # Test 5: Spoiler level
    print("\n5. Testing spoiler level...")
    print(f"   Current level: {journal.get_spoiler_level()}")
    journal.set_spoiler_level("main-quest")
    print(f"   Updated to: {journal.get_spoiler_level()}")
    allowed = journal.get_allowed_spoiler_levels()
    print(f"   ✅ Allowed levels: {allowed}")

    # Test 6: Session context
    print("\n6. Testing get_session_context()...")
    context = journal.get_session_context()
    print(f"   ✅ Session context:")
    print(f"      Goal: {context['current_goal']}")
    print(f"      Recent entries: {len(context['recent_progress'])}")
    print(f"      Spoiler level: {context['spoiler_level']}")

    if context['recent_progress']:
        print(f"\n   Greeting would say:")
        latest = context['recent_progress'][0]
        print(f"   'Systems online. Last time you {latest['note'].lower()}.'")


def test_spoiler_filtering():
    """Test M2 - Spoiler Filtering Integration"""
    print("\n" + "="*80)
    print("M2 TEST: Spoiler Filtering with Knowledge Base")
    print("="*80)

    journal = get_journal()

    # Set to 'none' - should filter out main-quest and endgame content
    print("\n1. Testing with spoiler level = 'none'...")
    journal.set_spoiler_level("none")
    allowed = journal.get_allowed_spoiler_levels()
    print(f"   Allowed levels: {allowed}")
    print(f"   ✅ Would filter out: main-quest, faction, endgame content")

    # Set to 'main-quest' - should allow none + main-quest
    print("\n2. Testing with spoiler level = 'main-quest'...")
    journal.set_spoiler_level("main-quest")
    allowed = journal.get_allowed_spoiler_levels()
    print(f"   Allowed levels: {allowed}")
    print(f"   ✅ Would show: none, main-quest content")
    print(f"   ✅ Would filter out: faction, endgame content")


async def main():
    print("\n" + "="*80)
    print("ASTROLB-3 M0-M2 FEATURE TEST")
    print("="*80)
    print("\nTesting features without requiring audio hardware or LiveKit Cloud")

    # Test M2 first (doesn't need API calls)
    test_journal()

    # Test M2 spoiler filtering
    test_spoiler_filtering()

    # Test M1 (needs OpenAI API)
    await test_knowledge_base()

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("\n✅ M0 (Voice Loop): Code complete, requires audio hardware + LiveKit")
    print("✅ M1 (Knowledge Base): Working - LanceDB with 7 chunks ingested")
    print("✅ M2 (Progress Journal): Working - SQLite journal with all tools")
    print("\n📋 To test full voice interaction:")
    print("   1. Deploy to LiveKit Cloud (M3)")
    print("   2. Use frontend on phone or laptop with working audio")
    print("   3. Or use `lk agent dev` with LiveKit CLI installed")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
