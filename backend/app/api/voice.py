from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from app.services.voice_service import voice_service

router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str
    lang: str = "en"


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio to text using Gemini multimodal."""
    audio_bytes = await audio.read()
    mime_type = audio.content_type or "audio/wav"
    transcribed_text = await voice_service.transcribe(audio_bytes, mime_type)
    return {"text": transcribed_text}


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """Convert text to speech audio (MP3) using gTTS."""
    audio_bytes = await voice_service.synthesize(request.text, request.lang)
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=speech.mp3"},
    )
