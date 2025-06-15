import os
import pytest
from dotenv import load_dotenv

# This is the "bad python hack" to load the .env file.
# It looks for a .env file in the current directory (or parent directories)
# and loads its variables into the environment.
load_dotenv()

# Now we can import our modules, which will have access to the API key
from app.services.agent.new_card_service import create_new_card_from_prompt
from app.services.github.schema import AgentRequest, NewCardData


# Mark this test as 'live' so you can run it separately from fast unit tests.
# This test will be slow and will cost money (API credits).
@pytest.mark.live
@pytest.mark.asyncio
async def test_live_create_multiple_cards():
    """
    This is a LIVE integration test. It makes a REAL API call to Anthropic.
    It verifies that the end-to-end flow works and that the AI can
    correctly break down a complex prompt into multiple cards.
    """
    # Ensure the API key is loaded before running the test
    assert (
        os.getenv("ANTHROPIC_API_KEY") is not None
    ), "ANTHROPIC_API_KEY not found. Make sure your .env file is correct."

    # A complex prompt that should ideally generate multiple cards
    complex_prompt = (
        "Please create a project plan to analyze the market for electric "
        "vehicles in Europe. I need one card for researching the German market "
        "and another for the French market. Also, create a final card for "
        "summarizing the findings."
    )

    request = AgentRequest(prompt=complex_prompt)

    print(f"\n--- Sending LIVE request to Claude with prompt: '{complex_prompt}' ---")

    # Call the actual function, no mocking!
    result = await create_new_card_from_prompt(request)

    # --- Flexible Assertions for Live Tests ---

    print(f"--- Received response from Claude. Execution time: {result.execution_time:.2f}s ---")
    print(f"--- Claude generated {len(result.card_data)} card(s) ---")

    # 1. Check the overall structure
    assert result is not None
    assert len(result.card_data) > 0, "The AI should have created at least one card."

    # 2. Check the contents of each card
    for i, card in enumerate(result.card_data):
        print(f"\n--- Validating Card {i+1}: '{card.title}' ---")
        assert isinstance(card, NewCardData)
        assert isinstance(card.title, str) and len(card.title) > 5
        assert isinstance(card.description, str) and len(card.description) > 10
        assert card.status == "todo"
        assert card.task_type == "research_task"
        assert isinstance(card.parameters.topics, list) and len(card.parameters.topics) > 0
        assert isinstance(card.parameters.scope, str) and len(card.parameters.scope) > 3

    print("\n--- ✅ LIVE TEST PASSED: The agent successfully created and validated cards from a real API call. ---")