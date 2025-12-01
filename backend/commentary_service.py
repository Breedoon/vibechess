"""
ElevenLabs-powered commentary service for generating audio from text.
"""
import os
import base64
import asyncio
import logging
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CommentaryService:
    """
    ElevenLabs-powered commentary audio generation.
    If ELEVENLABS_API_KEY is not set, it will skip audio generation.
    """

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        # Default voice ID, can be overridden via env
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
        self.enabled = bool(self.api_key)

        if self.enabled:
            logger.info(f"CommentaryService enabled with voice_id: {self.voice_id}")
        else:
            logger.info("CommentaryService disabled - no ELEVENLABS_API_KEY set")

    async def generate_audio(self, text: str) -> Optional[str]:
        """
        Generate audio from text using ElevenLabs API.

        Args:
            text: The commentary text to convert to speech

        Returns:
            Base64-encoded audio string, or None if disabled/failed
        """
        if not self.enabled or not text:
            return None

        # Run blocking HTTP request in executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._blocking_synthesize, text)

    def _blocking_synthesize(self, text: str) -> Optional[str]:
        """Synchronous audio synthesis using ElevenLabs API."""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.35,
                    "similarity_boost": 0.8,
                    "style": 0.85,
                    "use_speaker_boost": True
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            audio_bytes = response.content
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Commentary audio generation failed: {e}")
            return None


# Singleton instance
commentary_service = CommentaryService()
