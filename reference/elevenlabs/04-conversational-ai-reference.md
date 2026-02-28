# ElevenLabs Conversational AI (ElevenAgents) Reference

## Architecture

ElevenAgents coordinates four components:
1. Fine-tuned Speech-to-Text model
2. Choice of language model (incl. custom LLMs)
3. Low-latency Text-to-Speech across 70+ languages
4. Proprietary turn-taking model for conversation timing

## WebSocket Endpoint
```
wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}
```

## Authentication Methods

### WebSocket (Signed URL)
```python
# Server-side: get signed URL
resp = await http.get(
    f"https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id={AGENT_ID}",
    headers={"xi-api-key": ELEVENLABS_API_KEY}
)
signed_url = resp.json()["signed_url"]

# Client-side: connect with signed URL
conversation = await Conversation.startSession({ signedUrl })
```

### WebRTC (Conversation Token)
```python
# Server-side: get token
resp = await http.get(
    f"https://api.elevenlabs.io/v1/convai/conversation/token?agent_id={AGENT_ID}",
    headers={"xi-api-key": ELEVENLABS_API_KEY}
)
token = resp.json()["token"]

# Client-side: connect with token
conversation = await Conversation.startSession({ conversationToken: token, connectionType: "webrtc" })
```

## Python SDK — Full Example

```python
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

client = ElevenLabs(api_key="...")

# Register client tools
client_tools = ClientTools()

async def get_weather(params):
    location = params.get("location", "Unknown")
    return f"Weather in {location}: Sunny, 72F"

client_tools.register("get_weather", get_weather, is_async=True)

# Audio interface (16-bit PCM, mono, 16kHz, 250ms chunks)
audio_interface = DefaultAudioInterface()

# Create conversation
conversation = Conversation(
    client=client,
    agent_id="your-agent-id",
    requires_auth=True,
    audio_interface=audio_interface,
    client_tools=client_tools,
)

conversation.start_session()
# ... runs in background ...
conversation.end_session()
```

## Audio Interface Spec

All audio must conform to:
- **Format:** 16-bit PCM
- **Channels:** Mono (1 channel)
- **Sample Rate:** 16,000 Hz
- **Chunk Size:** 4000 samples (250ms) for input; 1000 samples (62.5ms) for output

### Custom Audio Interface
```python
from elevenlabs.conversational_ai.conversation import AudioInterface

class CustomAudioInterface(AudioInterface):
    def start(self, input_callback):
        """Initialize audio capture; call input_callback(audio_bytes) with mic data"""
        pass

    def stop(self):
        """Release audio resources"""
        pass

    def output(self, audio):
        """Play TTS audio (must return quickly, non-blocking)"""
        pass

    def interrupt(self):
        """Stop current playback immediately, clear buffers"""
        pass
```

## Conversation Event Flow

```
User speaks → Mic capture → Audio processing → Base64 encoding
→ Send `user_audio_chunk`

Server:
  Speech recognition → `user_transcript`
  LLM processing → `agent_response`
  TTS synthesis → Audio chunks
```

## Key Events

| Event | Description |
|-------|-------------|
| `conversation_initiation_metadata` | Session metadata at connection |
| `interruption` | User interrupts agent speech |
| `user_audio_chunk` | User audio sent to server |
| `user_transcript` | Transcribed user speech |
| `agent_response` | Agent's text response |
| Audio chunks | Synthesized agent speech |

## ADK (Agent Development Kit) Integration

ElevenLabs integrates with **Google's ADK** via MCP (Model Context Protocol):

```bash
uvx elevenlabs-mcp --api-key=YOUR_ELEVENLABS_API_KEY
```

Capabilities via MCP: TTS, STT, voice cloning, sound effects, conversational AI agent management, outbound calling.

## Data Residency

Regional servers available:
- **US:** `api.us.elevenlabs.io`
- **EU:** `api.eu.residency.elevenlabs.io`
- **India:** `api.in.residency.elevenlabs.io`

Enterprise: SOC 2, HIPAA, GDPR compliant. Zero-retention mode via `enable_logging=false`.
