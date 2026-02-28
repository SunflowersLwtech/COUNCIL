# ElevenLabs STT (Scribe) API Reference

## Models

| Model | ID | Use Case | Latency | Languages |
|-------|-----|----------|---------|-----------|
| Scribe v2 | `scribe_v2` | Batch/bulk transcription | Standard | 90+ |
| Scribe v2 Realtime | `scribe_v2_realtime` | Live streaming | ~150ms | 90+ |
| Scribe v1 (legacy) | `scribe_v1` | Batch transcription | Standard | 90+ |

## Endpoints

| Operation | Method | Path |
|-----------|--------|------|
| Create Transcript | `POST` | `/v1/speech-to-text` |
| Realtime STT | WebSocket | `wss://api.elevenlabs.io/v1/speech-to-text/realtime` |
| Get Transcript | `GET` | `/v1/speech-to-text/{transcription_id}` |
| Delete Transcript | `DELETE` | `/v1/speech-to-text/{transcription_id}` |
| Single-Use Token | `POST` | `/v1/single-use-token/realtime_scribe` |

## Batch Transcription Parameters

```
model_id                enum     required   "scribe_v1" | "scribe_v2"
file                    binary   conditional   Audio/video file (max 3GB)
cloud_storage_url       string   conditional   HTTPS URL (max 2GB)
language_code           string   optional   ISO 639-1/3 code, auto-detect if omitted
tag_audio_events        boolean  default: true
diarize                 boolean  default: false   Speaker diarization (up to 32 speakers)
num_speakers            integer  optional   1-32, auto-detect if null
timestamps_granularity  enum     default: "word"   "none" | "word" | "character"
keyterms                array    optional   Up to 100 terms (extra cost)
entity_detection        string/array  optional   "all" | ["pii","phi","pci","other","offensive_language"]
```

## Realtime WebSocket Parameters

```
model_id                    string   "scribe_v2_realtime"
token                       string   Single-use auth token
audio_format                enum     default: "pcm_16000"
language_code               string   optional
commit_strategy             enum     "manual" | "vad"
vad_silence_threshold_secs  number   default: 1.5
vad_threshold               number   default: 0.4
include_timestamps          boolean  default: false
include_language_detection  boolean  default: false
```

### Supported Realtime Audio Formats
`pcm_8000`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `pcm_48000`, `ulaw_8000`

### Client → Server Messages
```json
{
  "message_type": "input_audio_chunk",
  "audio_base_64": "<base64_encoded_audio>",
  "commit": false,
  "sample_rate": 16000,
  "previous_text": "optional context"
}
```

### Server → Client Messages
- `session_started` — Session ID and config
- `partial_transcript` — Interim results (may change)
- `committed_transcript` — Finalized text
- `committed_transcript_with_timestamps` — Finalized text with word-level timing

### WebSocket Error Types
`auth_error`, `quota_exceeded`, `commit_throttled`, `rate_limited`, `queue_overflow`,
`resource_exhausted`, `session_time_limit_exceeded`, `input_error`,
`chunk_size_exceeded`, `insufficient_audio_activity`, `transcriber_error`

## Python SDK Examples

### Batch Transcription
```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="...")

with open("audio.mp3", "rb") as f:
    transcription = client.speech_to_text.convert(
        file=f,
        model_id="scribe_v2",       # Use v2 instead of v1!
        tag_audio_events=True,
        diarize=True,
        language_code="eng",
    )

print(transcription.text)
print(transcription.words)
```

### Realtime Streaming (Server-side)
```python
import asyncio
from elevenlabs import ElevenLabs, RealtimeEvents, RealtimeAudioOptions, AudioFormat, CommitStrategy

client = ElevenLabs(api_key="...")

async def main():
    connection = await client.speech_to_text.realtime.connect(RealtimeAudioOptions(
        model_id="scribe_v2_realtime",
        audio_format=AudioFormat.PCM_16000,
        sample_rate=16000,
        commit_strategy=CommitStrategy.MANUAL,
        include_timestamps=True,
    ))

    connection.on(RealtimeEvents.PARTIAL_TRANSCRIPT, lambda d: print(f"Partial: {d.get('text','')}"))
    connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT, lambda d: print(f"Final: {d.get('text','')}"))
    connection.on(RealtimeEvents.ERROR, lambda e: print(f"Error: {e}"))

asyncio.run(main())
```

## Single-Use Token (for Client-Side Auth)

Server-side:
```python
# Generate token for frontend
import httpx

async with httpx.AsyncClient() as http:
    resp = await http.post(
        "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
    )
    token = resp.json()["token"]  # expires after 15 minutes
```

Client-side (browser):
```typescript
import { Scribe, RealtimeEvents } from "@elevenlabs/client";

const scribe = Scribe.connect({
    token: token,
    modelId: "scribe_v2_realtime",
    microphone: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
    },
});

scribe.on(RealtimeEvents.PARTIAL_TRANSCRIPT, (data) => console.log("Partial:", data.text));
scribe.on(RealtimeEvents.COMMITTED_TRANSCRIPT, (data) => console.log("Final:", data.text));
```

## Supported Audio/Video Formats (Batch)

**Audio:** AAC, AIFF, FLAC, M4A, MP3, OGG, Opus, WAV, WebM
**Video:** MP4, AVI, MKV, MOV, WMV, FLV, WebM, MPEG, 3GPP

## Language Support

- **Tier 1 (<=5% WER):** 35 languages incl. English, Spanish, French, German, Chinese, Japanese, Korean, etc.
- **Tier 2 (5-10% WER):** 20 languages
- **Tier 3 (10-20% WER):** 18 languages
- 90+ languages total
