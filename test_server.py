"""
Tests for the Edge-TTS OpenAI Compatible Server.

Includes:
- pytest tests using httpx (TestClient) for unit testing
- pytest tests using the OpenAI SDK for integration testing
- A curl-based test script (run with: python test_server.py)

The httpx tests run against FastAPI's TestClient (no server needed).
The OpenAI SDK and curl tests require the server to be running on localhost:8000.
"""

import subprocess
import json
import tempfile
import os

import pytest
from httpx import ASGITransport, AsyncClient

from server import app

BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Part 1: pytest + httpx (TestClient) — no running server needed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_models_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    model_ids = [m["id"] for m in data["data"]]
    assert "tts-1" in model_ids
    assert "tts-1-hd" in model_ids


@pytest.mark.asyncio
async def test_voices_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.get("/v1/voices")
    assert resp.status_code == 200
    data = resp.json()
    assert "voices" in data
    assert len(data["voices"]) > 0
    # Each voice should have a ShortName
    assert "ShortName" in data["voices"][0]


@pytest.mark.asyncio
async def test_speech_default_voice():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.post("/v1/audio/speech", json={
            "model": "tts-1",
            "input": "Hello, this is a test.",
        })
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_speech_chinese_voice():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.post("/v1/audio/speech", json={
            "model": "tts-1",
            "input": "你好，这是一个测试。",
            "voice": "zh-CN-XiaoxiaoNeural",
        })
    assert resp.status_code == 200
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_speech_with_speed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.post("/v1/audio/speech", json={
            "model": "tts-1",
            "input": "Speed test.",
            "voice": "alloy",
            "speed": 1.5,
        })
    assert resp.status_code == 200
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_speech_all_openai_voices():
    voices = ["alloy", "ash", "echo", "fable", "onyx", "nova", "shimmer"]
    for voice in voices:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post("/v1/audio/speech", json={
                "model": "tts-1",
                "input": "Voice test.",
                "voice": voice,
            })
        assert resp.status_code == 200, f"Failed for voice: {voice}"
        assert len(resp.content) > 0, f"Empty audio for voice: {voice}"


@pytest.mark.asyncio
async def test_speech_missing_input():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.post("/v1/audio/speech", json={
            "model": "tts-1",
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_speech_invalid_speed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        resp = await client.post("/v1/audio/speech", json={
            "model": "tts-1",
            "input": "Test",
            "speed": 10.0,  # exceeds max 4.0
        })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Part 2: OpenAI SDK integration tests (requires running server)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_openai_sdk_speech():
    from openai import OpenAI

    client = OpenAI(base_url=f"{BASE_URL}/v1", api_key="not-needed")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input="Hello from OpenAI SDK test.",
        )
        response.stream_to_file(tmp_path)
        size = os.path.getsize(tmp_path)
        assert size > 0, "Generated audio file is empty"
        print(f"  [OpenAI SDK] Generated {size} bytes -> {tmp_path}")
    finally:
        os.unlink(tmp_path)


@pytest.mark.integration
def test_openai_sdk_chinese():
    from openai import OpenAI

    client = OpenAI(base_url=f"{BASE_URL}/v1", api_key="not-needed")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",  # mapped to zh-CN-XiaoxiaoNeural
            input="你好，这是 OpenAI SDK 的中文测试。",
        )
        response.stream_to_file(tmp_path)
        size = os.path.getsize(tmp_path)
        assert size > 0, "Generated audio file is empty"
        print(f"  [OpenAI SDK Chinese] Generated {size} bytes -> {tmp_path}")
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Part 3: curl-based tests (requires running server)
# ---------------------------------------------------------------------------

def run_curl_tests():
    """Run curl-based tests against a running server."""
    print("=" * 60)
    print("curl-based tests (server must be running on :8000)")
    print("=" * 60)

    # Test 1: GET /v1/models
    print("\n[curl] GET /v1/models")
    result = subprocess.run(
        ["curl", "-s", f"{BASE_URL}/v1/models"],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    assert data["object"] == "list"
    print(f"  OK — {len(data['data'])} models returned")

    # Test 2: GET /v1/voices
    print("\n[curl] GET /v1/voices")
    result = subprocess.run(
        ["curl", "-s", f"{BASE_URL}/v1/voices"],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    count = len(data["voices"])
    assert count > 0
    print(f"  OK — {count} voices available")

    # Test 3: POST /v1/audio/speech (English)
    print("\n[curl] POST /v1/audio/speech (English, alloy)")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    subprocess.run([
        "curl", "-s", "-o", tmp_path,
        "-X", "POST", f"{BASE_URL}/v1/audio/speech",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "tts-1",
            "input": "Hello, this is a curl test.",
            "voice": "alloy",
        }),
    ], check=True)
    size = os.path.getsize(tmp_path)
    assert size > 0, "Audio file is empty"
    print(f"  OK — {size} bytes -> {tmp_path}")
    os.unlink(tmp_path)

    # Test 4: POST /v1/audio/speech (Chinese, direct voice)
    print("\n[curl] POST /v1/audio/speech (Chinese, zh-CN-XiaoxiaoNeural)")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    subprocess.run([
        "curl", "-s", "-o", tmp_path,
        "-X", "POST", f"{BASE_URL}/v1/audio/speech",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "tts-1",
            "input": "你好，这是 curl 的中文测试。",
            "voice": "zh-CN-XiaoxiaoNeural",
        }),
    ], check=True)
    size = os.path.getsize(tmp_path)
    assert size > 0, "Audio file is empty"
    print(f"  OK — {size} bytes -> {tmp_path}")
    os.unlink(tmp_path)

    # Test 5: POST /v1/audio/speech with speed
    print("\n[curl] POST /v1/audio/speech (speed=1.5)")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    subprocess.run([
        "curl", "-s", "-o", tmp_path,
        "-X", "POST", f"{BASE_URL}/v1/audio/speech",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "tts-1",
            "input": "Speed test with curl.",
            "voice": "echo",
            "speed": 1.5,
        }),
    ], check=True)
    size = os.path.getsize(tmp_path)
    assert size > 0, "Audio file is empty"
    print(f"  OK — {size} bytes -> {tmp_path}")
    os.unlink(tmp_path)

    # Test 6: Validation error (missing input)
    print("\n[curl] POST /v1/audio/speech (missing input — expect 422)")
    result = subprocess.run([
        "curl", "-s", "-w", "%{http_code}",
        "-X", "POST", f"{BASE_URL}/v1/audio/speech",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"model": "tts-1"}),
    ], capture_output=True, text=True)
    status = result.stdout[-3:]
    assert status == "422", f"Expected 422, got {status}"
    print(f"  OK — got HTTP {status}")

    print("\n" + "=" * 60)
    print("All curl tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_curl_tests()
