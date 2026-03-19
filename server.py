import io
import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="Edge-TTS OpenAI Compatible Server")

# Mapping OpenAI voice names to edge-tts voice identifiers
VOICE_MAP = {
    "alloy": "en-US-EmmaMultilingualNeural",
    "ash": "en-US-AndrewMultilingualNeural",
    "echo": "en-US-BrianMultilingualNeural",
    "fable": "en-GB-SoniaNeural",
    "onyx": "en-US-AvaMultilingualNeural",
    "nova": "zh-CN-XiaoxiaoNeural",
    "shimmer": "zh-CN-XiaoyiNeural",
}

FORMAT_CONTENT_TYPE = {
    "mp3": "audio/mpeg",
    "opus": "audio/opus",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "wav": "audio/wav",
    "pcm": "audio/pcm",
}


class SpeechRequest(BaseModel):
    model: str = "tts-1"
    input: str = Field(..., max_length=4096)
    voice: str = "alloy"
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest):
    # Resolve voice: use mapping if it's an OpenAI name, otherwise treat as edge-tts voice directly
    voice = VOICE_MAP.get(request.voice, request.voice)

    # Convert speed to edge-tts rate string (e.g. 1.5 -> "+50%", 0.8 -> "-20%")
    rate_percent = round((request.speed - 1.0) * 100)
    rate = f"{rate_percent:+d}%"

    try:
        communicate = edge_tts.Communicate(
            text=request.input,
            voice=voice,
            rate=rate,
        )

        # Collect audio data
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        if buffer.tell() == 0:
            raise HTTPException(status_code=500, detail="No audio data generated")

        buffer.seek(0)
        content_type = FORMAT_CONTENT_TYPE.get(request.response_format, "audio/mpeg")

        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="speech.{request.response_format}"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/voices")
async def list_voices():
    """List available edge-tts voices (bonus endpoint)."""
    voices = await edge_tts.list_voices()
    return {"voices": voices}


@app.get("/v1/models")
async def list_models():
    """Compatibility endpoint for model listing."""
    return {
        "object": "list",
        "data": [
            {"id": "tts-1", "object": "model", "owned_by": "edge-tts"},
            {"id": "tts-1-hd", "object": "model", "owned_by": "edge-tts"},
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
