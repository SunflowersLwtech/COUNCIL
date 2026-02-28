"""ElevenLabs TTS/STT middleware for COUNCIL voice interactions."""

import os
import asyncio
import io
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()


def inject_emotion_tags(text: str, emotional_state) -> str:
    """Wrap text with ElevenLabs v3 audio tags based on emotional state."""
    if emotional_state.anger > 0.6:
        return f"[angry]{text}"
    if emotional_state.fear > 0.6:
        return f"[scared]{text}"
    if emotional_state.happiness > 0.7:
        return f"[excited]{text}"
    return text


class VoiceMiddleware:
    """Handles text-to-speech and speech-to-text for agent messages."""

    def __init__(self):
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.client = None
        if api_key:
            try:
                from elevenlabs import ElevenLabs
                self.client = ElevenLabs(api_key=api_key)
            except ImportError:
                pass
        self._voice_id_cache: dict[str, str] = {}
        self._character_voices: dict[str, str] = {}

    def set_character_voices(self, voice_map: dict[str, str]):
        """Set dynamic character->voice mapping for game characters.

        Args:
            voice_map: dict mapping character_id to voice name (e.g. {"abc123": "Sarah"})
        """
        self._character_voices.update(voice_map)

    @property
    def available(self) -> bool:
        return self.client is not None

    async def text_to_speech(self, text: str, agent_id: str) -> bytes | None:
        """Convert agent text response to speech audio.

        Returns MP3 audio bytes or None if TTS is unavailable.
        """
        if not self.available:
            return None

        # Check character voices first, then fall back to agent voices
        voice_name = self._character_voices.get(agent_id, "Sarah")
        voice_id = await self._resolve_voice_id(voice_name)

        try:
            audio_iter = await asyncio.to_thread(
                self.client.text_to_speech.convert,
                text=text,
                voice_id=voice_id,
                model_id="eleven_v3",
                output_format="mp3_44100_128",
            )
            buf = io.BytesIO()
            for chunk in audio_iter:
                buf.write(chunk)
            return buf.getvalue()
        except Exception:
            return None

    async def speech_to_text(self, audio_bytes: bytes) -> str | None:
        """Convert user speech audio to text.

        Returns transcribed text or None if STT is unavailable.
        """
        if not self.available:
            return None

        try:
            result = await asyncio.to_thread(
                self.client.speech_to_text.convert,
                audio=audio_bytes,
                model_id="scribe_v1",
            )
            return result.text
        except Exception:
            return None

    async def stream_tts(self, text: str, voice_id: str) -> AsyncGenerator[bytes, None]:
        """Stream TTS audio chunks as they arrive from ElevenLabs.

        Args:
            text: Text to convert to speech.
            voice_id: ElevenLabs voice name or ID.

        Yields:
            Audio chunks as bytes.
        """
        if not self.available:
            return

        resolved_id = await self._resolve_voice_id(voice_id)

        try:
            audio_iter = await asyncio.to_thread(
                self.client.text_to_speech.convert,
                text=text,
                voice_id=resolved_id,
                model_id="eleven_v3",
                output_format="mp3_44100_128",
            )
            for chunk in audio_iter:
                yield chunk
        except Exception:
            return

    async def generate_sfx(self, prompt: str, duration_seconds: float = 3.0) -> bytes | None:
        """Generate sound effects using ElevenLabs SFX API.

        Args:
            prompt: Description of the sound effect (e.g., "dramatic gavel strike").
            duration_seconds: Duration of the generated audio.

        Returns:
            MP3 audio bytes or None if unavailable.
        """
        if not self.available:
            return None

        try:
            audio_iter = await asyncio.to_thread(
                self.client.text_to_sound_effects.convert,
                text=prompt,
                duration_seconds=duration_seconds,
            )
            buf = io.BytesIO()
            for chunk in audio_iter:
                buf.write(chunk)
            return buf.getvalue()
        except Exception:
            return None

    async def _resolve_voice_id(self, voice_name: str) -> str:
        """Resolve a voice name to its ElevenLabs voice ID."""
        if voice_name in self._voice_id_cache:
            return self._voice_id_cache[voice_name]

        try:
            voices = await asyncio.to_thread(self.client.voices.get_all)
            target = voice_name.lower()
            for voice in voices.voices:
                name_lower = voice.name.lower()
                if name_lower == target or name_lower.startswith(target + " "):
                    self._voice_id_cache[voice_name] = voice.voice_id
                    return voice.voice_id
        except Exception:
            pass

        return voice_name
