import os
import base64
import pytest
from dotenv import load_dotenv

# This is the "bad python hack" to load the .env file.
# It finds and loads the .env file from the same directory or parent directories.
load_dotenv()

# Now we can import our modules, which will have access to the HF_TOKEN.
from app.services.agent.image_generation_logic import generate_image_for_task
from app.services.github.schema import ImageGenerationRequest


# Mark this test as 'live' so you can run it separately from fast unit tests.
# This test will be slow and will cost money (API credits).
@pytest.mark.live
@pytest.mark.asyncio
async def test_live_generate_image_directly():
    """
    This is a LIVE integration test that calls the image generation logic directly.
    It makes a REAL API call to Hugging Face and verifies the response.
    """
    # 1. Arrange: Prepare the request and check for the API key.
    assert (
        os.getenv("HF_TOKEN") is not None
    ), "HF_TOKEN not found. Make sure it's in your .env file."

    # A descriptive prompt for the image generation model
    prompt = "A vibrant, photorealistic image of a futuristic solar panel array in a lush Spanish valley at sunset."

    request = ImageGenerationRequest(prompt=prompt)

    print(f"\n--- Sending LIVE image generation request with prompt: '{prompt}' ---")

    # 2. Act: Call the actual function directly, no mocking!
    result = await generate_image_for_task(request)

    print(f"--- Received response from image generation logic ---")

    # 3. Assert: Check the response object for correctness.
    assert result is not None
    assert result.model_id == "stabilityai/stable-diffusion-xl-base-1.0"
    assert isinstance(result.image_base64, str)
    assert len(result.image_base64) > 1000, "Base64 string should be substantial."

    # Verify that the returned string is valid Base64 data.
    # This is the most important check.
    try:
        # Attempt to decode the Base64 string. If it fails, it raises an error.
        image_bytes = base64.b64decode(result.image_base64)
        # Optional: Check that the decoded bytes look like a PNG file header.
        assert image_bytes.startswith(b'\x89PNG'), "Decoded data does not look like a PNG file."
    except (TypeError, ValueError) as e:
        pytest.fail(f"The returned 'image_base64' string is not valid Base64. Error: {e}")

    # --- THIS IS THE NEW PART ---
    try:
        # 1. Decode the Base64 string back into binary image data
        image_bytes = base64.b64decode(result.image_base64)

        # 2. Define a filename for the output image
        output_filename = "generated_test_image.png"

        # 3. Write the binary data to a file
        #    The 'wb' mode is crucial for writing binary files.
        with open(output_filename, "wb") as image_file:
            image_file.write(image_bytes)

        print(f"\n--- ✅ Image successfully saved as '{output_filename}' in your project directory. ---")

    except (TypeError, ValueError) as e:
        pytest.fail(f"The returned 'image_base64' string is not valid Base64. Error: {e}")

    print("\n--- ✅ LIVE TEST PASSED: The agent successfully generated an image and returned valid Base64 data. ---")