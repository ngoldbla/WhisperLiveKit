"""
French text simplification module.
Simplifies French text while keeping it in French, using LLM APIs.
"""

import asyncio
import logging
from typing import Optional
import aiohttp
import os

logger = logging.getLogger(__name__)


class FrenchSimplifier:
    """Simplifies French text using LLM APIs."""

    def __init__(self, backend: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the French simplifier.

        Args:
            backend: LLM backend to use ("openai", "anthropic")
            api_key: API key for the LLM service (or set via env var)
            model: Model to use (defaults per backend)
        """
        self.backend = backend.lower()
        self.api_key = api_key
        self.model = model

        # Set defaults based on backend
        if self.backend == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.model = model or "gpt-4o-mini"  # Fast and cheap
            self.endpoint = "https://api.openai.com/v1/chat/completions"
        elif self.backend == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.model = model or "claude-3-5-haiku-20241022"  # Fast and cheap
            self.endpoint = "https://api.anthropic.com/v1/messages"
        else:
            raise ValueError(f"Unsupported backend: {backend}. Use 'openai' or 'anthropic'")

        if not self.api_key:
            raise ValueError(f"API key required for {self.backend}. Set {self.backend.upper()}_API_KEY environment variable.")

        self.system_prompt = """Tu es un assistant qui simplifie le français parlé.
Ton rôle : transformer des phrases françaises complexes en français plus simple, tout en gardant exactement le même sens.

Règles :
- Garde TOUJOURS le texte en français
- Utilise des mots plus courants et simples
- Raccourcis les phrases longues
- Élimine le jargon et les expressions compliquées
- Préserve le sens exact et les informations importantes
- Ne traduis JAMAIS vers une autre langue
- Si le texte est déjà simple, renvoie-le tel quel"""

        self.user_prompt_template = "Simplifie cette phrase française : {text}"

    async def simplify_text(self, text: str) -> str:
        """
        Simplify French text asynchronously.

        Args:
            text: The French text to simplify

        Returns:
            Simplified French text
        """
        if not text or not text.strip():
            return text

        try:
            if self.backend == "openai":
                return await self._simplify_openai(text)
            elif self.backend == "anthropic":
                return await self._simplify_anthropic(text)
        except Exception as e:
            logger.error(f"Simplification error: {e}")
            # Return original text if simplification fails
            return text

    async def _simplify_openai(self, text: str) -> str:
        """Simplify using OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt_template.format(text=text)}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error {response.status}: {error_text}")
                    return text

                result = await response.json()
                simplified = result["choices"][0]["message"]["content"].strip()
                logger.debug(f"Simplified '{text}' -> '{simplified}'")
                return simplified

    async def _simplify_anthropic(self, text: str) -> str:
        """Simplify using Anthropic API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": 0.3,
            "system": self.system_prompt,
            "messages": [
                {"role": "user", "content": self.user_prompt_template.format(text=text)}
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Anthropic API error {response.status}: {error_text}")
                    return text

                result = await response.json()
                simplified = result["content"][0]["text"].strip()
                logger.debug(f"Simplified '{text}' -> '{simplified}'")
                return simplified


async def simplify_french_text(text: str, simplifier: FrenchSimplifier) -> str:
    """
    Helper function to simplify French text.

    Args:
        text: The French text to simplify
        simplifier: FrenchSimplifier instance

    Returns:
        Simplified French text
    """
    return await simplifier.simplify_text(text)
