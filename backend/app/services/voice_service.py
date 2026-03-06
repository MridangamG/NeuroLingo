"""
Voice service for Speech-to-Text (via Gemini multimodal) and Text-to-Speech (via gTTS).
"""
import io
import base64
from typing import Optional
from google import genai
from google.genai import types
from gtts import gTTS
from app.services.retry import retry_with_backoff, get_gemini_client


class VoiceService:
    def __init__(self):
        pass

    async def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """
        Transcribe audio to text using Gemini's multimodal capabilities.
        """
        try:
            client = get_gemini_client()
            response = await retry_with_backoff(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            types.Part.from_text(
                                text="Transcribe this audio exactly as spoken. "
                                "Return ONLY the transcribed text, nothing else."
                            ),
                        ]
                    )
                ],
            )
            return response.text.strip()
        except Exception as e:
            print(f"[VoiceService] Transcription error: {e}")
            return f"Error transcribing audio: {str(e)}"

    async def synthesize(self, text: str, lang: str = "en") -> bytes:
        """
        Convert text to speech audio using gTTS.
        Returns MP3 audio bytes.
        """
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as e:
            print(f"[VoiceService] Synthesis error: {e}")
            raise


voice_service = VoiceService()
