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
            os.path.dirname(__file__), "../prompts/suit-ai.md"
        )
        with open(prompt_path, "r") as f:
            system_prompt = f.read()

        super().__init__(instructions=system_prompt)

    @function_tool
    async def get_current_date_and_time(self, context: RunContext) -> str:
        """Get the current date and time.

        Returns:
            The current date and time in a readable format
        """
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        return f"The current date and time is {current_datetime}"

    async def on_enter(self):
        """Called when agent session starts."""
        logger.info("AstroLB-3 session started")
        await self.session.generate_reply(
            instructions="Greet Carlos briefly as his suit AI coming online. Keep it to one short sentence."
        )

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
