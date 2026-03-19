# CLAUDE.md

## Project Overview

An OpenAI-compatible Text-to-Speech web server powered by Microsoft Edge TTS (`edge-tts`). It exposes the same `/v1/audio/speech` endpoint as OpenAI's TTS API, allowing any OpenAI SDK client to use it as a drop-in replacement.

## Tech Stack

- **Python 3** with **FastAPI** and **uvicorn**
- **edge-tts** for speech synthesis (uses Microsoft Edge's online TTS service)
- **pydantic** for request validation

## Project Structure

```
server.py          # Main application — all API routes
requirements.txt   # Python dependencies
```

## How to Run

```bash
pip install -r requirements.txt
python server.py   # Starts on http://0.0.0.0:8000
```

## Key Design Decisions

- OpenAI voice names (alloy, echo, etc.) are mapped to edge-tts voices via `VOICE_MAP` in server.py. Users can also pass any edge-tts voice name directly.
- Speed is converted from a float multiplier (OpenAI format) to a percentage string (edge-tts format).
- The `/v1/voices` endpoint is a bonus endpoint (not in OpenAI spec) that lists all available edge-tts voices.

## Development Commands

```bash
# Run the server
python server.py

# Test the speech endpoint
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Hello","voice":"alloy"}' \
  --output test.mp3

# List available voices
curl http://localhost:8000/v1/voices
```
