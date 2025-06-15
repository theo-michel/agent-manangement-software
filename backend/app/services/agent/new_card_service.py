import json
import logging
import time
import uuid
from typing import Dict, Any

import anthropic
from pydantic import ValidationError

# Using the requested import path
from app.services.github.schema import (
    AgentRequest,
    NewCardAgentResponse,
    NewCardData,
)

logger = logging.getLogger(__name__)

# --- One-Time Initialization ---
# This client is created once when the module is first imported.
claude_client = anthropic.AsyncAnthropic()
AGENT_ID = f"new-card-func-{str(uuid.uuid4())[:8]}"


def _get_system_prompt() -> str:
    """The 'magic' prompt that instructs the LLM."""
    return """
    You are an expert project management assistant. Your only job is to analyze a user's request and transform it into a structured JSON object for a new task card. You MUST respond ONLY with a single, valid JSON object. Do not add any explanations or markdown formatting. If the request is not a research task, respond with `{"error": "I can only handle research tasks."}`.
    """


async def create_new_card_from_prompt(
    agent_request: AgentRequest,
) -> NewCardAgentResponse:
    """Processes a prompt to create a structured card."""
    start_time = time.time()
    logger.info(f"Agent processing prompt: '{agent_request.prompt[:70]}...'")

    try:
        message = await claude_client.messages.create(
            # model="claude-opus-4-20250514",
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=_get_system_prompt(),
            messages=[{"role": "user", "content": agent_request.prompt}],
        )
        response_text = message.content[0].text
        card_json = json.loads(response_text)

        if "error" in card_json:
            raise ValueError(card_json["error"])

        card_data = NewCardData(**card_json)

    except (ValidationError, json.JSONDecodeError) as e:
        raise ValueError(f"AI model returned invalid data: {e}")
    except anthropic.APIError as e:
        raise RuntimeError(f"AI service is currently unavailable: {e}")

    execution_time = time.time() - start_time
    metadata = {
        "model_used": message.model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }

    return NewCardAgentResponse(
        card_data=card_data,
        agent_id=AGENT_ID,
        execution_time=execution_time,
        metadata=metadata,
    )