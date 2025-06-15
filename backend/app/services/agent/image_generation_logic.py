import asyncio
import base64
import io
import logging
import os
import time

from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from app.services.github.schema import (
    ImageGenerationRequest,
    ImageGenerationResponse,
)

logger = logging.getLogger(__name__)

# --- One-Time Initialization ---

# Define the model and initialize the client once when the module is loaded.
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN environment variable not set. Please add it to your .env file."
    )

# Initialize the client to call the Hugging Face Inference API
# We pass the token and the billing information for the hackathon.
inference_client = InferenceClient(
    model=MODEL_ID, token=HF_TOKEN, bill_to="agents-hack",
)


async def generate_image_for_task(
    request: ImageGenerationRequest,
) -> ImageGenerationResponse:
    """
    Generates an image using the Hugging Face Inference API and returns it
    as a Base64 string.
    """
    logger.info(f"Generating image for prompt: '{request.prompt[:70]}...'")
    start_time = time.time()

    try:
        # The client's text_to_image method is synchronous (blocking).
        # We run it in a separate thread to keep the server responsive.
        image = await asyncio.to_thread(
            inference_client.text_to_image, request.prompt
        )

        # Convert the returned PIL Image object to a Base64 string.
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes)
        img_str = img_base64.decode("utf-8")

    except HfHubHTTPError as e:
        # Handle specific API errors from Hugging Face
        logger.error(f"Hugging Face API error: {e}")
        raise RuntimeError(f"Image generation service failed: {e}")
    except Exception as e:
        # Handle other unexpected errors
        logger.error(f"An unexpected error occurred during image generation: {e}")
        raise RuntimeError("An unexpected error occurred.")

    execution_time = time.time() - start_time
    logger.info(f"Image generated successfully in {execution_time:.2f}s")

    return ImageGenerationResponse(image_base64=img_str, model_id=MODEL_ID)