import os
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class AIService:
    """
    Service for interacting with AI models for generating descriptions and embeddings.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.httpx_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=60.0,
        )
        
    async def generate_description(self, code: str, context: Optional[str] = None) -> str:
        """
        Generate a description for a code snippet using an LLM.
        
        Args:
            code: The code to describe
            context: Optional context about the code (e.g., repository, file path)
            
        Returns:
            A description of the code
        """
        try:
            # Construct the prompt
            prompt = f"Please describe what the following code does in a concise manner:\n\n{code}"
            if context:
                prompt += f"\n\nContext: {context}"
                
            # Make API call to OpenAI (or another LLM provider)
            response = await self.httpx_client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that describes code."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3,
                }
            )
            response.raise_for_status()
            
            # Extract and return the description
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            return "No description available."
            
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for text using an embedding model.
        
        Args:
            text: The text to embed
            
        Returns:
            A list of floats representing the embedding vector
        """
        try:
            # Make API call to OpenAI embeddings API
            response = await self.httpx_client.post(
                "https://api.openai.com/v1/embeddings",
                json={
                    "model": "text-embedding-ada-002",
                    "input": text,
                }
            )
            response.raise_for_status()
            
            # Extract and return the embedding
            result = response.json()
            return result["data"][0]["embedding"]
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []
            
    async def chat_completion(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """
        Generate a chat completion using a chat model.
        
        Args:
            messages: List of message dictionaries with role and content
            system_prompt: Optional system prompt to override the default
            
        Returns:
            The generated response
        """
        try:
            # Prepare messages with system prompt if provided
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            # Make API call to OpenAI
            response = await self.httpx_client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4",
                    "messages": chat_messages,
                    "temperature": 0.7,
                }
            )
            response.raise_for_status()
            
            # Extract and return the response
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return "I'm sorry, I couldn't generate a response at this time."
            
    async def close(self):
        """Close the HTTP client."""
        if self.httpx_client:
            await self.httpx_client.aclose() 