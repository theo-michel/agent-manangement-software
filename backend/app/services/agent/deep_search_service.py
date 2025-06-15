import asyncio
import logging
import os
import time
import uuid

from smolagents import CodeAgent, LiteLLMModel
from smolagents.default_tools import DuckDuckGoSearchTool

# Using the requested import path
from app.services.github.schema import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


def _create_agent() -> CodeAgent:
    """Initializes the expensive agent object."""
    logger.info("Initializing Deep Search Agent...")
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set.")

    model_id = "claude-sonnet-4-20250514"
    model = LiteLLMModel(model_id=model_id, temperature=0.1)
    search_tool = DuckDuckGoSearchTool()
    agent = CodeAgent(tools=[search_tool], model=model, max_steps=2)
    logger.info("Deep Search Agent created successfully!")
    return agent


# --- One-Time Initialization ---
# This agent is created once when the module is first imported.
deep_search_agent = _create_agent()
AGENT_ID = f"deep-search-func-{str(uuid.uuid4())[:8]}"


async def run_deep_search(agent_request: AgentRequest) -> AgentResponse:
    """Runs the agent with a user's prompt."""
    start_time = time.time()
    prompt = agent_request.prompt
    logger.info(f"Agent running search for: '{prompt[:70]}...'")

    try:
        # Run the synchronous agent.run in a separate thread
        final_answer = await asyncio.to_thread(deep_search_agent.run, prompt)
    except Exception as e:
        raise RuntimeError(f"Agent execution failed: {e}")

    execution_time = time.time() - start_time
    return AgentResponse(
        response=final_answer,
        agent_id=AGENT_ID,
        execution_time=execution_time,
        metadata={"prompt_length": len(prompt)},
    )