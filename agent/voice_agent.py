"""
AstroLB-3 Voice Agent for Starfield
====================================
LiveKit voice agent implementation for private suit AI companion.
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    WorkerOptions,
    cli,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.llm import function_tool
from livekit.plugins import openai, silero

from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Optional

# Import journal module
from journal import get_journal

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent configuration
AGENT_NAME = "astrolb3-starfield"


def prewarm(proc: JobProcess):
    """Prewarm models to reduce cold start latency."""
    proc.userdata["vad"] = silero.VAD.load()


class AstroLB3Assistant(Agent):
    """AstroLB-3 suit AI assistant with knowledge base and progress tracking."""

    def __init__(self):
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(__file__), "prompts/suit-ai.md"
        )
        with open(prompt_path, "r") as f:
            system_prompt = f.read()

        # Add knowledge base instruction
        enhanced_prompt = system_prompt + """

## Knowledge Base Tool Usage

When answering questions about Starfield mechanics, quests, locations, or strategies:
1. ALWAYS use the search_knowledge_base tool FIRST
2. Base your answer on the retrieved information
3. If no information is found, respond with: "My records don't show that. I may need an update to my database."
4. Never speculate or make up game information
"""

        super().__init__(instructions=enhanced_prompt)

        # Lazy-loaded knowledge base (None until first use)
        self._kb_table = None
        self._openai_client = None

        # Progress journal
        self._journal = get_journal()

    def _lazy_load_kb(self):
        """Lazily initialize knowledge base connection."""
        if self._kb_table is not None:
            return  # Already loaded

        try:
            import lancedb
            from openai import OpenAI

            db_path = Path(__file__).parent / "../data/lancedb"

            if not db_path.exists():
                logger.warning(f"Knowledge base not found at {db_path}")
                return

            db = lancedb.connect(str(db_path))
            table_name = "starfield_kb"

            if table_name not in db.table_names():
                logger.warning(f"Knowledge base table '{table_name}' not found")
                return

            self._kb_table = db.open_table(table_name)
            self._openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            logger.info("Knowledge base loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            # Don't raise - agent should continue without KB

    @function_tool
    async def search_knowledge_base(self, context: RunContext, query: str) -> str:
        """Search the Starfield knowledge base for relevant information.

        Use this tool to answer questions about Starfield mechanics, quests,
        locations, systems, factions, skills, ships, outposts, and strategies.

        Args:
            query: The search query or question about Starfield

        Returns:
            Relevant information from the knowledge base, or an error message
        """
        logger.info(f"Searching knowledge base: {query}")

        # Lazy load KB on first use
        if self._kb_table is None:
            self._lazy_load_kb()

        # If KB failed to load, return error message
        if self._kb_table is None or self._openai_client is None:
            logger.warning("Knowledge base unavailable")
            return "My records don't show that. I may need an update to my database."

        try:
            # Get query embedding
            response = self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            query_vector = response.data[0].embedding

            # Search (get more results than needed for spoiler filtering)
            results = self._kb_table.search(query_vector).limit(10).to_list()

            # Filter by spoiler level from journal
            allowed_levels = self._journal.get_allowed_spoiler_levels()
            filtered = [
                r for r in results
                if r.get("spoiler_level", "none") in allowed_levels
            ][:3]

            if not filtered:
                logger.info("No results found in knowledge base")
                return "My records don't show that. I may need an update to my database."

            # Format results
            context_parts = []
            for result in filtered:
                source = result.get("source", "Unknown")
                heading = result.get("heading", "")
                text = result.get("text", "")

                context_parts.append(f"[{source} - {heading}]\n{text}")

            combined = "\n\n".join(context_parts)
            logger.info(f"Found {len(filtered)} relevant chunks")

            return combined

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return "My records encountered an error during search. Continuing without that data."

    @function_tool
    async def get_current_date_and_time(self, context: RunContext) -> str:
        """Get the current date and time.

        Returns:
            The current date and time in a readable format
        """
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        return f"The current date and time is {current_datetime}"

    @function_tool
    async def log_progress(self, context: RunContext, note: str) -> str:
        """Log a progress entry to the journal.

        Use this when Carlos tells you about something he accomplished,
        discovered, or completed in Starfield.

        Args:
            note: Description of the progress (e.g., "Completed the first Constellation mission")

        Returns:
            Confirmation message
        """
        try:
            self._journal.log_progress(note)
            logger.info(f"Logged progress: {note}")
            return f"Progress logged: {note}"
        except Exception as e:
            logger.error(f"Error logging progress: {e}")
            return f"Failed to log progress: {str(e)}"

    @function_tool
    async def recall_progress(self, context: RunContext, topic: Optional[str] = None) -> str:
        """Recall recent progress entries from the journal.

        Use this when Carlos asks what he did last time, or wants to
        remember progress on a specific topic.

        Args:
            topic: Optional topic to filter by (e.g., "Neon", "outposts", "ship building")

        Returns:
            Recent progress entries, or message if none found
        """
        try:
            entries = self._journal.recall_progress(topic=topic, limit=10)

            if not entries:
                return "No progress entries found in your journal."

            # Format entries for voice output
            lines = []
            for entry in entries[:5]:  # Limit to 5 for voice
                timestamp = entry["timestamp"].split("T")[0]  # Just the date
                note = entry["note"]
                lines.append(f"{timestamp}: {note}")

            result = "Journal entries:\n" + "\n".join(lines)
            logger.info(f"Recalled {len(entries)} progress entries")
            return result

        except Exception as e:
            logger.error(f"Error recalling progress: {e}")
            return f"Failed to recall progress: {str(e)}"

    @function_tool
    async def set_current_goal(self, context: RunContext, goal: str) -> str:
        """Set the current goal.

        Use this when Carlos tells you what he's planning to do next or
        wants to set a new objective.

        Args:
            goal: The new goal (e.g., "Find a Class C ship" or "Complete Ryujin questline")

        Returns:
            Confirmation message
        """
        try:
            self._journal.set_current_goal(goal)
            logger.info(f"Set current goal: {goal}")
            return f"Current goal set: {goal}"
        except Exception as e:
            logger.error(f"Error setting goal: {e}")
            return f"Failed to set goal: {str(e)}"

    @function_tool
    async def set_spoiler_level(self, context: RunContext, level: str) -> str:
        """Set the spoiler level for knowledge base filtering.

        Use this when Carlos wants to change how much plot information
        he's willing to see.

        Args:
            level: Spoiler level - must be one of: none, main-quest, faction, endgame

        Returns:
            Confirmation message
        """
        try:
            self._journal.set_spoiler_level(level)
            logger.info(f"Set spoiler level: {level}")
            return f"Spoiler level set to: {level}. I'll filter knowledge base results accordingly."
        except ValueError as e:
            logger.warning(f"Invalid spoiler level: {level}")
            return f"Invalid spoiler level. Must be: none, main-quest, faction, or endgame."
        except Exception as e:
            logger.error(f"Error setting spoiler level: {e}")
            return f"Failed to set spoiler level: {str(e)}"

    async def on_enter(self):
        """Called when agent session starts."""
        logger.info("AstroLB-3 session started")

        # Get session context from journal
        context = self._journal.get_session_context()
        current_goal = context.get("current_goal")
        recent_progress = context.get("recent_progress", [])

        # Build greeting instructions with context
        if current_goal or recent_progress:
            context_info = []
            if current_goal:
                context_info.append(f"Current goal: {current_goal}")
            if recent_progress:
                # Include just the most recent entry
                latest = recent_progress[0]
                context_info.append(f"Last progress: {latest['note']}")

            instructions = f"""Greet Carlos briefly as his suit AI coming online.
Include context from the journal: {' | '.join(context_info)}
Keep the greeting to 1-2 sentences. Sound like you remember where he left off."""
        else:
            instructions = "Greet Carlos briefly as his suit AI coming online. Since there's no journal history, ask what he's working on. Keep it to one short sentence."

        await self.session.generate_reply(instructions=instructions)

    async def on_exit(self):
        """Called when agent session ends."""
        logger.info("AstroLB-3 session ended")


async def entrypoint(ctx: JobContext):
    """Main entry point for the agent worker."""

    logger.info(f"AstroLB-3 agent started in room: {ctx.room.name}")

    # Get model configuration from environment
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    stt_model = os.getenv("STT_MODEL", "whisper-1")
    tts_model = os.getenv("TTS_MODEL", "tts-1")
    tts_voice = os.getenv("TTS_VOICE", "onyx")

    logger.info(f"Configuration: LLM={llm_model}, STT={stt_model}, TTS={tts_model}/{tts_voice}")

    # Configure the voice pipeline
    session = AgentSession(
        # Speech-to-Text (OpenAI Whisper)
        stt=openai.STT(
            model=stt_model,
        ),

        # Large Language Model (OpenAI GPT)
        llm=openai.LLM(
            model=llm_model,
            temperature=0.7,
        ),

        # Text-to-Speech (OpenAI TTS)
        tts=openai.TTS(
            model=tts_model,
            voice=tts_voice,
            speed=1.0,
        ),

        # Voice Activity Detection (Silero VAD)
        vad=silero.VAD.load(),

        # Turn detection strategy (multilingual model)
        turn_detection=MultilingualModel(),
    )

    # Start the session with AstroLB-3 assistant
    await session.start(
        room=ctx.room,
        agent=AstroLB3Assistant(),
    )

    # Event handlers for monitoring
    @session.on("agent_state_changed")
    def on_state_changed(ev):
        """Log agent state changes."""
        logger.info(f"State: {ev.old_state} -> {ev.new_state}")

    @session.on("user_started_speaking")
    def on_user_speaking():
        """Track when user starts speaking."""
        logger.debug("User started speaking")

    @session.on("user_stopped_speaking")
    def on_user_stopped():
        """Track when user stops speaking."""
        logger.debug("User stopped speaking")


if __name__ == "__main__":
    # Run the agent with explicit worker name
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name=AGENT_NAME,
        )
    )
