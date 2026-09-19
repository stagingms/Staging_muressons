"""
ElevenLabs TTS Integration — Voice synthesis for CEO Interview
==============================================================

Provides text-to-speech using the ElevenLabs REST API v1.
Audio is returned as base64-encoded MP3 for easy frontend consumption.

Usage:
    from elevenlabs_tts import synthesize_speech
    audio_b64 = await synthesize_speech("Hello, I'm the CEO.", voice_id="21m00Tcm4TlvDq8ikWAM")
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import Optional

import httpx

from config import ELEVENLABS_API_KEY

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Voice settings tuned for professional CEO interview tone
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.65,           # Slightly above default for consistency
    "similarity_boost": 0.75,    # Good likeness to the selected voice
    "style": 0.3,                # Mild expressiveness
    "use_speaker_boost": True,
}

# Default model — multilingual v2 for natural speech
DEFAULT_MODEL_ID = "eleven_multilingual_v2"


async def synthesize_speech(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel (female default)
    model_id: str = DEFAULT_MODEL_ID,
    voice_settings: Optional[dict] = None,
    output_format: str = "mp3_44100_128",
) -> Optional[str]:
    """Synthesize speech from text using ElevenLabs API.
    
    Args:
        text: The text to synthesize (max ~5000 chars per call)
        voice_id: ElevenLabs voice ID
        model_id: TTS model to use
        voice_settings: Override voice stability/similarity settings
        output_format: Audio format string
        
    Returns:
        Base64-encoded audio string, or None if synthesis fails.
    """
    api_key = ELEVENLABS_API_KEY
    if not api_key:
        print("[elevenlabs] No API key configured. Set ELEVENLABS_API_KEY in .env")
        return None

    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings or DEFAULT_VOICE_SETTINGS,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                audio_bytes = response.content
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                print(f"[elevenlabs] Synthesized {len(audio_bytes)} bytes for voice {voice_id}")
                return audio_b64
            else:
                print(f"[elevenlabs] API error {response.status_code}: {response.text[:200]}")
                return None
    except httpx.TimeoutException:
        print("[elevenlabs] Request timed out")
        return None
    except Exception as e:
        print(f"[elevenlabs] Synthesis failed: {e}")
        return None


async def synthesize_interview_audio(
    persona: dict,
    text_segments: list[str],
) -> list[Optional[str]]:
    """Synthesize multiple text segments for the interview flow.
    
    Args:
        persona: CEO persona dict with elevenlabs_voice_id
        text_segments: List of text strings to synthesize
        
    Returns:
        List of base64-encoded audio strings (None for failures)
    """
    voice_id = persona.get("elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM")
    tasks = [
        synthesize_speech(
            text=segment,
            voice_id=voice_id,
        )
        for segment in text_segments
    ]
    return list(await asyncio.gather(*tasks))


async def check_api_status() -> dict:
    """Check if ElevenLabs API is reachable and the key is valid.
    
    Returns:
        {"available": bool, "subscription": dict|None, "error": str|None}
    """
    api_key = ELEVENLABS_API_KEY
    if not api_key:
        return {"available": False, "subscription": None, "error": "No API key configured"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/user/subscription",
                headers={"xi-api-key": api_key},
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "subscription": {
                        "tier": data.get("tier"),
                        "character_count": data.get("character_count"),
                        "character_limit": data.get("character_limit"),
                        "remaining": (data.get("character_limit", 0) - data.get("character_count", 0)),
                    },
                    "error": None,
                }
            else:
                return {"available": False, "subscription": None, "error": f"API returned {response.status_code}"}
    except Exception as e:
        return {"available": False, "subscription": None, "error": str(e)}
