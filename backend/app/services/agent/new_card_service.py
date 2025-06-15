import asyncio
import json
import logging
import time
import uuid


import anthropic
from pydantic import ValidationError

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
    Updated prompt to instruct the LLM to create tasks with dependencies.
    """
    return """
    You are an expert project manager. Your job is to analyze a user's request and break it down into a series of logical, actionable task cards with dependencies.

    You MUST respond with a single JSON object with a single key, "cards", containing a list of task card objects.

    For EACH card in the list, you MUST:
    1.  Assign a unique `card_id` string (e.g., "task-1", "task-2"). This ID is temporary and local to this response.
    2.  Fill out the card details (`title`, `description`, etc.).
    3.  Determine the `task_type`. Use `research_task` for investigation and `phone_task` for calling experts or team members to inform them of results.
    4.  Crucially, for any card that depends on another, add the prerequisite card's `card_id` to its `dependencies` list. The first task(s) should have an empty `dependencies` list.

    **Correct JSON Output Structure Example:**
    ```json
    {
      "cards": [
        {
          "card_id": "task-1",
          "title": "Research German EV Market",
          "description": "Analyze the German market for electric vehicles.",
          "task_type": "research_task",
          "status": "todo",
          "parameters": { "topics": ["market size", "key players"], "scope": "Market Analysis" },
          "dependencies": []
        },
        {
          "card_id": "task-2",
          "title": "Call Supervisor",
          "description": "Inform supervisor of the results of the market research.",
          "task_type": "phone_task",
          "status": "todo",
          "parameters": null,
          "dependencies": ["task-1"]
        }
      ]
    }
    ```
    """

def _extract_json_from_response(text: str) -> str:
    """
    Finds and extracts a JSON object from a string, even if it's wrapped
    in markdown code fences.
    """
    # Find the first '{' which marks the beginning of the JSON
    start_index = text.find('{')
    # Find the last '}' which marks the end of the JSON
    end_index = text.rfind('}')

    if start_index == -1 or end_index == -1:
        raise ValueError("No valid JSON object found in the AI response.")

    return text[start_index : end_index + 1]


async def create_new_card_from_prompt(
    agent_request: AgentRequest,
) -> NewCardAgentResponse:
    """
    Processes a prompt to create one or more structured cards with dependencies.
    """
    start_time = time.time()
    logger.info(f"Agent processing prompt: '{agent_request.prompt[:70]}...'")

    max_retries = 3
    base_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            message = await claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=5000,  # Increased for more complex structures
                system=_get_system_prompt(),
                messages=[{"role": "user", "content": agent_request.prompt}],
            )

            response_text = message.content[0].text
            cleaned_json_text = _extract_json_from_response(response_text)
            response_json = json.loads(cleaned_json_text)

            if "error" in response_json:
                raise ValueError(response_json["error"])

            card_list_json = response_json.get("cards")
            if not isinstance(card_list_json, list):
                raise ValueError("AI response is missing the 'cards' list.")

            # Validate each card and then validate the dependency graph
            validated_cards = [NewCardData(**card) for card in card_list_json]
            _validate_dependencies(validated_cards)
            
            # Success, break out of retry loop
            break

        except (ValidationError, json.JSONDecodeError, TypeError) as e:
            logger.error(f"AI response failed validation: {e}")
            raise ValueError(f"AI model returned invalid data: {e}")
        except anthropic.APIError as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit or overload error
            if ("overloaded" in error_msg or "rate limit" in error_msg or "429" in error_msg or "529" in error_msg) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Anthropic API overloaded/rate limited (attempt {attempt + 1}/{max_retries}). Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"Anthropic API error: {e}")
                raise RuntimeError(f"AI service is currently unavailable after {attempt + 1} attempts: {e}")

    execution_time = time.time() - start_time
    metadata = {
        "model_used": message.model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "card_count": len(validated_cards),
        "attempts_made": attempt + 1,
    }

    return NewCardAgentResponse(
        card_data=validated_cards,
        agent_id=AGENT_ID,
        execution_time=execution_time,
        metadata=metadata,
    )


def _validate_dependencies(cards: list[NewCardData]):
    """
    Ensures that all listed dependencies refer to card_ids that actually exist.
    """
    all_card_ids = {card.card_id for card in cards}
    for card in cards:
        for dep_id in card.dependencies:
            if dep_id not in all_card_ids:
                raise ValueError(
                    f"Invalid dependency graph: Card '{card.title}' depends on "
                    f"non-existent card_id '{dep_id}'."
                )