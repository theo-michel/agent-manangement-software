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
    """
    A more robust system prompt to strictly guide the LLM's JSON output.
    """
    # This is the updated, more assertive prompt.
    return """
    You are an expert project management assistant. Your ONLY job is to analyze a user's request and transform it into a structured JSON object that follows a strict schema.

    You MUST output ONLY a single, valid JSON object. Do not add any text, explanations, or markdown formatting like ```json.

    The JSON object MUST have EXACTLY these fields: `title`, `description`, `task_type`, `status`, and `parameters`.
    - The `task_type` field MUST be `research_task`.
    - The `parameters` field MUST be an object containing `topics` (a list of strings) and `scope` (a string).

    DO NOT invent any other fields. Your output must conform precisely to the example below.

    **Correct JSON Output Structure Example:**
    ```json
    {
      "title": "Research Ed-Tech Market in France",
      "description": "Analyze the current market size, key players, and growth trends for educational technology in France.",
      "task_type": "research_task",
      "status": "todo",
      "parameters": {
        "topics": ["market size", "key players", "growth trends", "AI-powered tools"],
        "scope": "Market Analysis"
      }
    }
    ```
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
            logger.error(f"Error: {card_json['error']}")
            raise ValueError(card_json["error"])

        card_data = NewCardData(**card_json)

    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"JSON Content {card_json}")
        logger.error(f"Error: {e}")
        raise ValueError(f"AI model returned invalid data: {e}")
    except anthropic.APIError as e:
        logger.error(f"Error: {e}")
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