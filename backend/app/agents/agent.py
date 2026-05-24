import datetime
import logging

from pydantic_ai import Agent

from app.core.config import settings

logger = logging.getLogger(__name__)

agent = Agent(
    model=f"anthropic:{settings.anthropic_model}",
    system_prompt="You are a helpful assistant. Use the available tools when they can answer the question.",
)


@agent.tool_plain
def get_current_time() -> str:
    """Return the current UTC time."""
    now = datetime.datetime.now(datetime.UTC)
    logger.debug("get_current_time called, returning %s", now)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")
