"""Neural Text-To-Speech (TTS) Service for LARA OS.
Provides lifelike, studio-grade neural voice synthesis using Edge TTS and gTTS fallback.
"""

import os
import re
import io
import base64
import logging
import asyncio
from typing import Optional

logger = logging.getLogger("lara.services.voice")


class VoiceTTSService:
    """High-fidelity Neural Text-To-Speech synthesizer with studio female resonance."""

    def __init__(self):
        # en-US-JennyNeural is Microsoft's top-rated natural, warm, conversational female voice
        self.default_voice = "en-US-JennyNeural"
        self.alternative_voice = "en-US-AriaNeural"

    def clean_text_for_speech(self, raw_text: str) -> str:
        """Thoroughly strip markdown, symbols, code blocks, and emojis for crystal-clear spoken audio."""
        text = raw_text
        # Strip code blocks
        text = re.sub(r"```[\s\S]*?```", "Code execution output is displayed on your screen.", text)
        # Strip markdown bold/italic/inline
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)
        # Strip markdown links: [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Strip URLs
        text = re.sub(r"https?://\S+", "link", text)
        # Strip headers, list bullets, table bars, quote signs
        text = re.sub(r"#+\s*", "", text)
        text = re.sub(r"^[\s*\-•>|]+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"[|\\/_{}~^]+", " ", text)
        # Clean multiple newlines and spaces
        text = re.sub(r"\n+", ". ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:800] if len(text) > 800 else text

    async def generate_speech_bytes(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """Synthesize text into MP3 audio bytes using edge-tts with fallback to gTTS."""
        cleaned = self.clean_text_for_speech(text)
        if not cleaned:
            cleaned = "Understood, Bunty."

        target_voice = voice or self.default_voice

        # 1. Try Edge TTS (Ultra-high quality Microsoft Jenny Neural Voice)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                cleaned,
                voice=target_voice,
                rate=rate,
                pitch=pitch
            )
            mp3_bytes = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_bytes.extend(chunk["data"])
            if mp3_bytes:
                return bytes(mp3_bytes)
        except Exception as e:
            logger.warning("Edge-TTS error: %s, falling back to gTTS", e)

        # 2. Fallback to Google TTS (gTTS)
        try:
            from gtts import gTTS
            tts = gTTS(text=cleaned, lang="en", tld="com", slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e2:
            logger.error("gTTS fallback failed: %s", e2)

        return b""

    async def generate_speech_base64(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> str:
        """Synthesize text into Base64 data URI string (data:audio/mp3;base64,...)."""
        audio_bytes = await self.generate_speech_bytes(text, voice=voice)
        if not audio_bytes:
            return ""
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return f"data:audio/mp3;base64,{b64}"


voice_service = VoiceTTSService()
