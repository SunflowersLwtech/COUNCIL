# COUNCIL — ElevenLabs Integration Analysis & Issues

## Current Implementation Summary

### Backend (tts_middleware.py)
- **TTS:** `client.text_to_speech.convert()` with `eleven_v3`, `mp3_44100_128`
- **STT:** `client.speech_to_text.convert()` with `scribe_v1` ← **OUTDATED**
- **SFX:** `client.text_to_sound_effects.convert()`
- **Voice Resolution:** Name → ID via `client.voices.get_all()`, cached
- **Emotion Tags:** `inject_emotion_tags()` wraps text with `[angry]`, `[scared]`, `[excited]`

### Frontend (useVoice.ts)
- **STT:** ElevenLabs Scribe via `@elevenlabs/client` → `Scribe.connect()` with `scribe_v2_realtime`
- **Fallback:** Web Speech API when Scribe fails
- **TTS:** Fetch MP3 from backend `/api/voice/tts`, play via HTML5 Audio
- **Queue:** Pre-fetches next TTS while current plays

### Server Endpoints
- `POST /api/voice/tts` — Sync TTS generation
- `POST /api/voice/tts/stream` — Streaming TTS
- `POST /api/voice/scribe-token` — Single-use token for frontend Scribe
- `POST /api/voice/sfx` — Sound effects

---

## Identified Issues

### 1. STT: Backend uses `scribe_v1` (DEPRECATED)

**File:** `backend/voice/tts_middleware.py:100`
```python
model_id="scribe_v1",  # Should be "scribe_v2"
```

**Impact:** Scribe v1 is legacy. Scribe v2 has significantly better WER, supports diarization, entity detection, keyterm prompting.

**Fix:** Change to `scribe_v2`.

### 2. STT: Backend `speech_to_text.convert()` uses wrong parameter name

**File:** `backend/voice/tts_middleware.py:98-99`
```python
result = await asyncio.to_thread(
    self.client.speech_to_text.convert,
    audio=audio_bytes,       # ← Might be wrong parameter name
    model_id="scribe_v1",
)
```

**Expected API:** The SDK `speech_to_text.convert()` takes `file` parameter (file-like object), not `audio` (raw bytes).

**Fix:**
```python
audio_file = io.BytesIO(audio_bytes)
result = await asyncio.to_thread(
    self.client.speech_to_text.convert,
    file=audio_file,
    model_id="scribe_v2",
)
```

### 3. STT: No HTTP endpoint for batch STT

The backend `speech_to_text()` method exists but is NOT exposed via any HTTP endpoint. The frontend uses Scribe real-time directly, but there's no REST endpoint for uploading audio files for transcription.

**Impact:** Limited to real-time STT only; no file upload transcription.

### 4. TTS: `stream_tts()` uses `convert()` not `stream()`

**File:** `backend/voice/tts_middleware.py:122-128`
```python
audio_iter = await asyncio.to_thread(
    self.client.text_to_speech.convert,  # ← Should be .stream() for streaming
    text=text,
    voice_id=resolved_id,
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)
```

**Impact:** The "stream" endpoint actually waits for full generation before yielding chunks (just chunking the complete response), not true streaming from ElevenLabs. This defeats the purpose of the streaming endpoint.

**Fix:** Use `self.client.text_to_speech.stream()` instead for actual streaming.

### 5. TTS: Emotion tags are minimal

**File:** `backend/voice/tts_middleware.py:15-23`

Only 3 emotion tags are mapped (angry, scared, excited). The v3 model supports many more: `[whispers]`, `[sighs]`, `[sarcastic]`, `[curious]`, `[crying]`, `[laughs]`, `[appalled]`, etc.

**Impact:** Under-utilizing v3's expressive capability.

### 6. Frontend: Scribe token endpoint error handling

**File:** `frontend/hooks/useVoice.ts:137-148`

The token fetch uses a relative URL `/api/voice/scribe-token` which depends on the Next.js proxy being configured correctly. If `NEXT_PUBLIC_API_URL` is set (as used in other API calls via `api.ts`), this call may hit the wrong server.

**Fix:** Use `${API_BASE}/api/voice/scribe-token` consistently.

### 7. Scribe token endpoint may return wrong shape

**File:** `backend/server.py:71-78`

The backend forwards the raw ElevenLabs response. The ElevenLabs API returns `{"token": "..."}`. The frontend expects `data.token`. This should be fine, but there's no explicit validation.

### 8. No retry/exponential backoff for TTS

All TTS calls have basic try/except but no retry logic. Rate limiting (429) would silently fail.

### 9. Voice resolution inefficiency

`_resolve_voice_id()` calls `client.voices.get_all()` for every uncached voice name. This fetches ALL voices every time. For the first few requests this causes unnecessary latency.

**Fix:** Pre-fetch and cache all voices on startup (or first TTS call).

---

## Recommended Improvements

### Priority 1: Fix STT
1. Update `scribe_v1` → `scribe_v2` in `tts_middleware.py`
2. Fix parameter name `audio` → `file` (wrap in BytesIO)
3. Add `tag_audio_events=True` and optional `diarize=True`

### Priority 2: Fix Streaming TTS
1. Change `stream_tts()` from `.convert()` to `.stream()`
2. Consider using `eleven_flash_v2_5` for streaming endpoints (75ms latency vs standard)

### Priority 3: Consistency
1. Use `API_BASE` consistently in frontend for scribe-token fetch
2. Add error retry with exponential backoff for TTS/STT calls

### Priority 4: Enhancement
1. Expand emotion tag mapping for v3
2. Add voice settings (stability, similarity_boost) as configurable parameters
3. Pre-cache voice ID resolution on middleware init
4. Consider adding `language_code` parameter for better multilingual support
5. Add batch STT endpoint for file upload transcription

---

## Architecture Recommendation

```
Current Flow:
  Frontend → /api/voice/scribe-token → ElevenLabs Token API
  Frontend → Scribe.connect(token) → ElevenLabs WebSocket STT
  Frontend → /api/voice/tts → Backend → ElevenLabs HTTP TTS → MP3 → Frontend

Improved Flow (for lower latency):
  Frontend → /api/voice/scribe-token → ElevenLabs Token API
  Frontend → Scribe.connect(token) → ElevenLabs WebSocket STT (same, works well)
  Frontend → /api/voice/tts/stream → Backend → ElevenLabs Stream TTS → Chunked MP3 → Frontend
                                                  ↑ Use eleven_flash_v2_5 for ~75ms TTFB
```
