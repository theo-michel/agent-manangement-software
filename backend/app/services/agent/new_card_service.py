import json
import logging
import time
import uuid
from typing import Dict, Any

import anthropic
from pydantic import ValidationError

from app.services.github.schema import (
    AgentRequest,
    NewCardAgentResponse,
    NewCardData,
)

logger = logging.getLogger(__name__)

claude_client = anthropic.AsyncAnthropic()
AGENT_ID = f"new-card-func-{str(uuid.uuid4())[:8]}"


def _get_system_prompt() -> str:
    """
    Updated prompt to instruct the LLM to break down a request into a
    list of cards.
    """
    return """
    You are an expert project manager. Your job is to analyze a user's request and break it down into a series of logical, actionable task cards.

    You MUST respond with a single JSON object. This object must have a single key, "cards", which contains a list of task card objects.

    For each card in the list, you MUST adhere to this schema:
    - `title`: A concise, action-oriented title.
    - `description`: A clear description of the specific sub-task.
    - `task_type`: This MUST be `research_task`.
    - `status`: This MUST be `todo`.
    - `parameters`: An object containing `topics` (a list of strings) and `scope` (a string).

    If the user's request is simple and only requires one card, return a list containing that single card. If the request is complex, break it down into multiple cards.

    **Correct JSON Output Structure Example:**
    ```json
    {
      "cards": [
        {
          "title": "Analyze French Ed-Tech Market",
          "description": "Conduct a market analysis of the French educational technology sector, focusing on market size and key players.",
          "task_type": "research_task",
          "status": "todo",
          "parameters": {
            "topics": ["market size", "key players", "growth trends"],
            "scope": "Market Analysis"
          }
        },
        {
          "title": "Research German AI Learning Tools",
          "description": "Investigate the landscape of AI-powered language learning tools specifically within Germany.",
          "task_type": "research_task",
          "status": "todo",
          "parameters": {
            "topics": ["AI tools", "language learning", "competitor features"],
            "scope": "Competitor Overview"
          }
        }
      ]
    }
    ```
    """


async def create_new_card_from_prompt(
    agent_request: AgentRequest,
) -> NewCardAgentResponse:
    """
    Processes a prompt to create one or more structured cards.
    """
    start_time = time.time()
    logger.info(f"Agent processing prompt: '{agent_request.prompt[:70]}...'")

    try:
        message = await claude_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,  # Increased tokens for potentially larger lists
            system=_get_system_prompt(),
            messages=[{"role": "user", "content": agent_request.prompt}],
        )

        response_text = message.content[0].text
        response_json = json.loads(response_text)

        if "error" in response_json:
            raise ValueError(response_json["error"])

        # Extract the list of cards from the 'cards' key
        card_list_json = response_json.get("cards")
        if card_list_json is None:
            raise ValueError("AI response is missing the 'cards' list.")

        # Validate each card in the list using a list comprehension
        validated_cards = [NewCardData(**card) for card in card_list_json]

    except (ValidationError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"AI response failed validation: {e}")
        raise ValueError(f"AI model returned invalid data: {e}")
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise RuntimeError(f"AI service is currently unavailable: {e}")

    execution_time = time.time() - start_time
    metadata = {
        "model_used": message.model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "card_count": len(validated_cards),
    }

    return NewCardAgentResponse(
        card_data=validated_cards,
        agent_id=AGENT_ID,
        execution_time=execution_time,
        metadata=metadata,
    )