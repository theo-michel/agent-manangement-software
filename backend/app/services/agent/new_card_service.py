import json
import logging
import time
import uuid
from typing import Dict, Any

import anthropic
from pydantic import ValidationError

from app.services.github.schema import AgentRequest, NewCardAgentResponse, NewCardData

logger = logging.getLogger(__name__)

def _get_system_prompt(self) -> str:
    """The 'magic' prompt that instructs the LLM. Keep this powerful."""
    return """
    You are an expert project management assistant. Your only job is to analyze a user's request and transform it into a structured JSON object for a new task card.

    1.  **Analyze & Classify**: Determine if the request is a `research_task`. If it's not about research, you MUST respond with a JSON error object: `{"error": "I can only handle research tasks."}`.
    2.  **Extract Details**: For a `research_task`, extract the `title`, `description`, and the `parameters` (`topics` and `scope`).
    3.  **Format Output**: You MUST respond ONLY with a single, valid JSON object. Do not add any explanations or markdown formatting.
    """

async def process_prompt(
    self, agent_request: AgentRequest
) -> NewCardAgentResponse:
    """Uses Claude to process the prompt and create a structured card."""
    start_time = time.time()
    self.logger.info(f"Agent processing prompt: '{agent_request.prompt[:70]}...'")

    try:
        message = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": agent_request.prompt}],
        )
        response_text = message.content[0].text
        card_json = json.loads(response_text)

        if "error" in card_json:
            # The model understood but rejected the prompt. This is a user error.
            raise ValueError(card_json["error"])

        # Pydantic validates the structure. If it fails, it's a model error.
        card_data = NewCardData(**card_json)

    except (ValidationError, json.JSONDecodeError) as e:
        self.logger.error(f"AI model returned invalid data: {e}")
        raise ValueError("The AI model's output was malformed or invalid.")
    except anthropic.APIError as e:
        self.logger.error(f"Anthropic API error: {e}")
        raise RuntimeError("The AI service is currently unavailable.")

    execution_time = time.time() - start_time
    metadata = {
        "model_used": message.model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }

    return NewCardAgentResponse(
        card_data=card_data,
        agent_id=self.agent_id,
        execution_time=execution_time,
        metadata=metadata,
    )