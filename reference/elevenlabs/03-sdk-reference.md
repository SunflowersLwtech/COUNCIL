# ElevenLabs SDK Reference

## Package Overview

| Package | Platform | Purpose | Install |
|---------|----------|---------|---------|
| `elevenlabs` | Python | Server-side TTS, STT, voice mgmt, conversational AI | `pip install elevenlabs` |
| `elevenlabs[pyaudio]` | Python | + Audio I/O for desktop apps | `pip install elevenlabs[pyaudio]` |
| `@elevenlabs/elevenlabs-js` | Node.js | Server-side TTS, STT, voice mgmt | `npm install @elevenlabs/elevenlabs-js` |
| `@elevenlabs/client` | Browser | Conversational AI + Scribe (vanilla JS) | `npm install @elevenlabs/client` |
| `@elevenlabs/react` | React | Conversational AI + Scribe (React hooks) | `npm install @elevenlabs/react` |
| `@elevenlabs/react-native` | React Native | Mobile conversational AI | `npm install @elevenlabs/react-native` |

## Python SDK

### Installation
```bash
pip install elevenlabs>=1.0.0
```

Latest: v2.36.1 (Feb 2026). Requires Python 3.8+.

### Client Initialization
```python
from elevenlabs.client import ElevenLabs, AsyncElevenLabs

# Sync client (auto-reads ELEVENLABS_API_KEY env var)
client = ElevenLabs()
client = ElevenLabs(api_key="...", timeout=240)

# Async client
async_client = AsyncElevenLabs(api_key="...")
```

### Key Imports
```python
# Core
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import ElevenLabs  # alternative
from elevenlabs import VoiceSettings, ApiError
from elevenlabs.play import play, stream

# Realtime STT
from elevenlabs import RealtimeEvents, RealtimeUrlOptions, RealtimeAudioOptions
from elevenlabs import AudioFormat, CommitStrategy

# Conversational AI
from elevenlabs.conversational_ai.conversation import Conversation, AsyncConversation, ClientTools
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
```

### TTS Methods
```python
# Sync convert (returns iterator of bytes)
audio = client.text_to_speech.convert(text=..., voice_id=..., model_id=..., output_format=...)

# Sync stream (returns chunked iterator)
audio_stream = client.text_to_speech.stream(text=..., voice_id=..., model_id=...)

# With timestamps
result = client.text_to_speech.convert_with_timestamps(voice_id=..., text=..., output_format=...)
# result.audio_base64, result.alignment, result.normalized_alignment

# Access headers (cost tracking)
response = client.text_to_speech.with_raw_response.convert(...)
char_cost = response.headers.get("x-character-count")
```

### STT Methods
```python
# Batch transcription
transcription = client.speech_to_text.convert(
    file=open("audio.mp3", "rb"),
    model_id="scribe_v2",
    tag_audio_events=True,
    diarize=True,
)
# transcription.text, transcription.words, transcription.language_code

# Realtime connection
connection = await client.speech_to_text.realtime.connect(RealtimeAudioOptions(...))
```

### Voice Management
```python
# Search voices
response = client.voices.search()
for v in response.voices:
    print(f"{v.name}: {v.voice_id}")

# Get all voices
all_voices = client.voices.get_all()

# Instant voice clone
voice = client.voices.ivc.create(
    name="Alex",
    description="...",
    files=["sample.mp3"],
)
```

### Sound Effects
```python
audio = client.text_to_sound_effects.convert(
    text="dramatic thunder",
    duration_seconds=3.0,
)
```

### Single-Use Token
```python
token_response = client.tokens.singleUse.create("realtime_scribe")
token = token_response.token  # expires after 15 minutes
```

## JavaScript Client SDK (@elevenlabs/client)

### Scribe (Real-time STT in Browser)
```typescript
import { Scribe, RealtimeEvents } from "@elevenlabs/client";

const scribe = Scribe.connect({
    token: "your-token",
    modelId: "scribe_v2_realtime",
    microphone: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
    },
});

scribe.on(RealtimeEvents.OPEN, () => { /* connected */ });
scribe.on(RealtimeEvents.PARTIAL_TRANSCRIPT, (data) => { /* interim text */ });
scribe.on(RealtimeEvents.COMMITTED_TRANSCRIPT, (data) => { /* final text */ });
scribe.on(RealtimeEvents.ERROR, (error) => { /* handle error */ });
scribe.on(RealtimeEvents.AUTH_ERROR, (data) => { /* auth failed */ });
scribe.on(RealtimeEvents.CLOSE, () => { /* disconnected */ });

// Manual commit
scribe.commit();

// Close connection
scribe.close();
```

### Conversation (Conversational AI in Browser)
```typescript
import { Conversation } from "@elevenlabs/client";

const conversation = await Conversation.startSession({
    agentId: "<your-agent-id>",
    connectionType: "webrtc",  // or "websocket"
    onConnect: () => {},
    onDisconnect: () => {},
    onMessage: (msg) => {},
    onError: (err) => {},
    onStatusChange: ({ status }) => {},
    onModeChange: ({ mode }) => {},
    clientTools: { ... },
    overrides: {
        tts: { voiceId: "...", speed: 1.0, stability: 0.5, similarityBoost: 0.8 },
    },
});

conversation.endSession();
conversation.setVolume({ volume: 0.8 });
conversation.setMicMuted(false);
conversation.sendUserMessage("text message");
```

## React SDK (@elevenlabs/react)

### useScribe Hook
```tsx
import { useScribe, CommitStrategy } from "@elevenlabs/react";

function Component() {
    const scribe = useScribe({
        modelId: "scribe_v2_realtime",
        commitStrategy: CommitStrategy.AUTOMATIC,
        onPartialTranscript: (data) => console.log("Partial:", data.text),
        onCommittedTranscript: (data) => console.log("Final:", data.text),
        onError: (error) => console.error(error),
    });

    const start = async () => {
        const token = await fetchTokenFromServer();
        await scribe.connect({ token, microphone: { echoCancellation: true, noiseSuppression: true } });
    };

    return (
        <div>
            <button onClick={start} disabled={scribe.isConnected}>Start</button>
            <button onClick={scribe.disconnect}>Stop</button>
            <p>Live: {scribe.partialTranscript}</p>
            {scribe.committedTranscripts.map(t => <p key={t.id}>{t.text}</p>)}
        </div>
    );
}
```

### useConversation Hook
```tsx
import { useConversation } from "@elevenlabs/react";

const conversation = useConversation({
    onConnect: () => {},
    onMessage: (msg) => {},
    onError: (err) => {},
    onStatusChange: ({ status }) => {},
    onModeChange: ({ mode }) => {},
});

await conversation.startSession({ agentId: "...", connectionType: "webrtc" });
// conversation.status, conversation.isSpeaking, conversation.canSendFeedback
```
