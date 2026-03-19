# Edge-TTS OpenAI Compatible Server

A lightweight, drop-in replacement for OpenAI's Text-to-Speech API, powered by Microsoft Edge TTS via the [edge-tts](https://github.com/rany2/edge-tts) library. Free, no API key required.

## Features

- **OpenAI API compatible** — works with any OpenAI SDK client
- **300+ voices** — supports all Microsoft Edge TTS voices across 40+ languages
- **Multiple formats** — MP3, Opus, AAC, FLAC, WAV, PCM
- **Speed control** — adjustable from 0.25x to 4.0x
- **Zero cost** — uses Microsoft Edge's free TTS service

## Quick Start

### Using Docker (recommended)

```bash
docker run -d -p 8000:8000 lewangdev/folotoy-edge-tts
```

Or build the image locally:

```bash
docker build -t folotoy-edge-tts .
docker run -d -p 8000:8000 folotoy-edge-tts
```

### Using Docker Compose

```yaml
services:
  edge-tts:
    image: lewangdev/folotoy-edge-tts
    ports:
      - "8000:8000"
    restart: unless-stopped
```

```bash
docker compose up -d
```

### Using pip

```bash
pip install -r requirements.txt
python server.py
```

The server starts on `http://0.0.0.0:8000`.

## API Endpoints

### POST `/v1/audio/speech`

Fully compatible with [OpenAI's TTS API](https://platform.openai.com/docs/api-reference/audio/createSpeech).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `tts-1` | Model name (accepted for compatibility) |
| `input` | string | *required* | Text to synthesize (max 4096 chars) |
| `voice` | string | `alloy` | OpenAI voice name or any edge-tts voice |
| `response_format` | string | `mp3` | `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm` |
| `speed` | float | `1.0` | Speed multiplier (0.25 to 4.0) |

**OpenAI voice mapping:**

| OpenAI Voice | Edge-TTS Voice |
|---|---|
| `alloy` | `en-US-EmmaMultilingualNeural` |
| `ash` | `en-US-AndrewMultilingualNeural` |
| `echo` | `en-US-BrianMultilingualNeural` |
| `fable` | `en-GB-SoniaNeural` |
| `onyx` | `en-US-AvaMultilingualNeural` |
| `nova` | `zh-CN-XiaoxiaoNeural` |
| `shimmer` | `zh-CN-XiaoyiNeural` |

You can also use any edge-tts voice directly (e.g., `zh-CN-YunxiNeural`, `ja-JP-NanamiNeural`).

### GET `/v1/voices`

Lists all available edge-tts voices with metadata (locale, gender, etc.).

### GET `/v1/models`

Returns compatible model list for OpenAI SDK compatibility.

## Usage Examples

### curl

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Hello, world!","voice":"alloy"}' \
  --output speech.mp3
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello, world!",
)
response.stream_to_file("output.mp3")
```

### Chinese TTS

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"你好，世界！","voice":"zh-CN-XiaoxiaoNeural"}' \
  --output speech.mp3
```

## License

MIT
