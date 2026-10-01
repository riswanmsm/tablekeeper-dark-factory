import asyncio
import logging
import os
from pathlib import Path
from band import Agent, Emit, configure_logging
from band.adapters import ClaudeSDKAdapter
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dark-factory-seat")
async def main():
    configure_logging(root_level="INFO")
    role = os.environ["SEAT_ROLE"]
    agent_id = os.environ["BAND_AGENT_ID"]
    api_key = os.environ["BAND_API_KEY"]
    mandate_path = Path(f"/mandates/{role}.md")
    mandate_text = mandate_path.read_text(encoding="utf-8")
    # Uses ClaudeSDKAdapter (or swap with GeminiAdapter / CodexAdapter / LangGraphAdapter)
    adapter = ClaudeSDKAdapter(
        model=os.getenv("MODEL_NAME", "claude-sonnet-4-5"),
        cwd="/workspace",
        permission_mode="bypassPermissions",  # Safe because it's locked inside Docker /workspace!
        custom_section=mandate_text,
        emit={Emit.TOOL_CALLS, Emit.THOUGHTS, Emit.USAGE},
    )
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.getenv("BAND_WS_URL", "wss://app.band.ai/api/v1/socket/websocket"),
        rest_url=os.getenv("BAND_REST_URL", "https://app.band.ai"),
    )
    logger.info(f"Seat '{role}' online and connected to BAND room (/workspace isolated)")
    await agent.run()
if __name__ == "__main__":
    asyncio.run(main())