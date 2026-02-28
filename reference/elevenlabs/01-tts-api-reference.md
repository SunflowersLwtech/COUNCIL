# ElevenLabs TTS API Reference

## Endpoints

| Operation | Method | Path |
|-----------|--------|------|
| Convert (sync) | `POST` | `/v1/text-to-speech/{voice_id}` |
| Stream | `POST` | `/v1/text-to-speech/{voice_id}/stream` |
| Convert with Timestamps | `POST` | `/v1/text-to-speech/{voice_id}/with-timestamps` |
| Stream with Timestamps | `POST` | `/v1/text-to-speech/{voice_id}/stream/with-timestamps` |
| WebSocket (single context) | `WSS` | `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input` |
| WebSocket (multi context) | `WSS` | `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/multi-stream-input` |

## Request Parameters (Convert / Stream)

```
text              string   required   Content for conversion
model_id          string   default: "eleven_multilingual_v2"
language_code     string   ISO 639-1 language code
output_format     string   default: "mp3_44100_128"
voice_settings    object   See below
speed             double   0.7-1.2, default: 1.0
seed              integer  0-4294967295, deterministic sampling
previous_text     string   Context for speech continuity
next_text         string   Context for speech continuity
previous_request_ids  array  Up to 3 request IDs for multi-part
next_request_ids      array  Up to 3 request IDs for multi-part
pronunciation_dictionary_locators  array  Up to 3 dictionaries
apply_text_normalization  string  "auto" | "on" | "off"
```

## Voice Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `stability` | 0.0-1.0 | 0.5 | Higher = consistent/monotone; Lower = expressive |
| `similarity_boost` | 0.0-1.0 | 0.75 | Voice character matching |
| `style` | 0.0-1.0 | 0.0 | Style exaggeration (v2+ only). Keep at 0 |
| `use_speaker_boost` | boolean | true | Speaker similarity; adds latency. Not for v3 |
| `speed` | 0.7-1.2 | 1.0 | Speech pace |

## Models

| Model | ID | Languages | Char Limit | Latency | Cost |
|-------|----|-----------|------------|---------|------|
| Eleven v3 | `eleven_v3` | 70+ | 5,000 | Standard | Standard |
| Multilingual v2 | `eleven_multilingual_v2` | 29 | 10,000 | Standard | Standard |
| Flash v2.5 | `eleven_flash_v2_5` | 32 | 40,000 | ~75ms | 50% lower |
| Turbo v2.5 | `eleven_turbo_v2_5` | 32 | 40,000 | ~250-300ms | 50% lower |

**Important**: WebSockets are NOT available for `eleven_v3` model.

## Output Formats

**MP3:** `mp3_22050_32`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`
**PCM:** `pcm_8000`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`
**Opus:** `opus_48000_32`, `opus_48000_64`, `opus_48000_96`, `opus_48000_128`, `opus_48000_192`
**Telephony:** `ulaw_8000`, `alaw_8000`

## v3 Audio Tags (Emotion Control)

```
[laughs]  [whispers]  [sighs]  [sarcastic]  [curious]
[excited]  [crying]  [angry]  [scared]  [appalled]
```

Example: `"[appalled] Are you serious? [sighs] I can't believe that!"`

## Python SDK Examples

### Basic Convert
```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="...")

audio = client.text_to_speech.convert(
    text="Hello world",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)

with open("output.mp3", "wb") as f:
    for chunk in audio:
        if chunk:
            f.write(chunk)
```

### Streaming
```python
from elevenlabs import VoiceSettings

audio_stream = client.text_to_speech.stream(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Streaming example",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.8,
        style=0.0,
        use_speaker_boost=True,
        speed=1.0,
    ),
)

for chunk in audio_stream:
    if chunk:
        process(chunk)
```

### Async Client
```python
from elevenlabs.client import AsyncElevenLabs

client = AsyncElevenLabs(api_key="...")

audio = await client.text_to_speech.convert(
    text="Hello async world!",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
)
```

## Error Handling

```python
from elevenlabs import ApiError

try:
    audio = client.text_to_speech.convert(...)
except ApiError as e:
    if e.status_code == 429:
        # Rate limited — exponential backoff
        pass
    elif e.status_code in (400, 401, 403):
        # Non-retriable
        raise
```

## Concurrency Limits by Plan

| Plan | Multilingual v2 / v3 | Turbo / Flash |
|------|-----------------------|---------------|
| Free | 2 | 4 |
| Starter | 3 | 6 |
| Creator | 5 | 10 |
| Pro | 10 | 20 |
| Scale | 15 | 30 |

## Best Practices

1. **Voice selection matters most** (Voice > Model > Settings)
2. **Break long text into segments** (<800 chars) with `previous_text`/`next_text` for continuity
3. **Use Flash v2.5** for real-time/low-latency (~75ms TTFB, 50% lower cost)
4. **Disable `use_speaker_boost`** to reduce latency
5. **Keep `style` at 0** to avoid extra computation
6. **Use PCM output** (`pcm_16000`) for lowest encoding overhead
7. **Pre-normalize text**: spell out numbers, expand abbreviations
8. **Cache frequently used outputs** for consistency
9. **Use regional servers** closest to your infrastructure
