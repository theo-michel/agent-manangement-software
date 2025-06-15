import os
import pytest
from dotenv import load_dotenv

# Load .env file for the API key
load_dotenv()

from app.services.agent.new_card_service import create_new_card_from_prompt
from app.services.github.schema import AgentRequest, NewCardData, TaskType


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_create_cards_with_dependencies():
    """
    A LIVE integration test that checks if the AI can create a sequence
    of tasks with dependencies (e.g., research THEN report).
    """
    assert (
        os.getenv("ANTHROPIC_API_KEY") is not None
    ), "ANTHROPIC_API_KEY not found in .env file."

    # A prompt that explicitly asks for a sequence of tasks
    dependency_prompt = (
        "First, I need to research the market for solar panels in Spain. "
        "After that is done, create a summary report of the findings for the leadership team."
    )

    request = AgentRequest(prompt=dependency_prompt)

    print(f"\n--- Sending LIVE request to Claude with prompt: '{dependency_prompt}' ---")

    result = await create_new_card_from_prompt(request)

    print(f"--- Received response. Execution time: {result.execution_time:.2f}s ---")
    print(f"--- Claude generated {len(result.card_data)} card(s) ---")

    # --- Assertions for Dependency Logic ---

    assert len(result.card_data) >= 2, "Should create at least a research and a report card."

    # Find the research and report cards
    research_cards = [
        c for c in result.card_data if c.task_type == TaskType.RESEARCH
    ]
    report_cards = [
        c for c in result.card_data if c.task_type == TaskType.REPORTING
    ]

    assert len(research_cards) > 0, "At least one research card should exist."
    assert len(report_cards) == 1, "Exactly one report card should exist."

    report_card = report_cards[0]
    research_card_ids = {card.card_id for card in research_cards}

    print(f"Report Card: '{report_card.title}'")
    print(f"  - Dependencies: {report_card.dependencies}")
    print(f"Research Card IDs: {research_card_ids}")

    # The crucial check: The report card must depend on the research card(s).
    assert len(report_card.dependencies) > 0, "Report card should have dependencies."
    assert all(
        dep in research_card_ids for dep in report_card.dependencies
    ), "Report card must depend on the generated research cards."

    # The research card(s) should have no dependencies
    for research_card in research_cards:
        assert (
            len(research_card.dependencies) == 0
        ), "Initial research cards should have no dependencies."

    print("\n--- ✅ LIVE TEST PASSED: The agent successfully created a task chain with valid dependencies. ---")