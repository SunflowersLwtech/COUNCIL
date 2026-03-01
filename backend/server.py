"""FastAPI server for COUNCIL Game — voice + game endpoints."""

import os
import json
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from backend.voice.tts_middleware import VoiceMiddleware, inject_emotion_tags
from backend.game.orchestrator import GameOrchestrator
from backend.game.persistence import PersistenceManager
from backend.game.skill_loader import SkillLoader
from backend.models.game_models import GameChatRequest, GameVoteRequest, PlayerNightActionRequest

load_dotenv()

import logging
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


# ── App setup ─────────────────────────────────────────────────────────

voice: VoiceMiddleware | None = None
game_orchestrator: GameOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global voice, game_orchestrator
    voice = VoiceMiddleware()
    persistence = PersistenceManager()
    await persistence.connect()
    game_orchestrator = GameOrchestrator(persistence=persistence)
    yield
    await persistence.close()


app = FastAPI(title="COUNCIL API", version="0.2.0", lifespan=lifespan)

_default_origins = "http://localhost:3000,http://localhost:5173"
_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Voice TTS endpoint ────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    agent_id: str = "orchestrator"


@app.post("/api/voice/scribe-token")
async def scribe_token():
    """Get a single-use token for ElevenLabs Scribe real-time STT."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "ELEVENLABS_API_KEY not configured"})

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe",
            headers={"xi-api-key": api_key},
        )
    if resp.status_code != 200:
        return JSONResponse(status_code=resp.status_code, content={"error": "Failed to get scribe token"})
    return resp.json()


@app.post("/api/voice/tts")
async def voice_tts(request: TTSRequest):
    """Generate TTS audio for an agent response."""
    if not voice or not voice.available:
        return JSONResponse(
            status_code=503,
            content={"error": "Voice not available"},
        )

    audio = await voice.text_to_speech(request.text, request.agent_id)
    if audio:
        return Response(content=audio, media_type="audio/mpeg")
    return JSONResponse(
        status_code=502,
        content={"error": "TTS generation failed"},
    )


# ── Dependency: require orchestrator ──────────────────────────────────

def _require_orchestrator() -> GameOrchestrator:
    """Return the orchestrator or raise 503 if not initialized."""
    if game_orchestrator is None:
        raise HTTPException(status_code=503, detail="Service not ready — game orchestrator not initialized")
    return game_orchestrator


# ── COUNCIL Game Endpoints ────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "ok"}


@app.get("/api/skills")
async def list_skills():
    """List all available agent skills."""
    orch = _require_orchestrator()
    return {"skills": orch.skill_loader.list_skills()}


@app.get("/api/game/scenarios")
async def game_scenarios():
    """List available pre-built game scenarios."""
    orch = _require_orchestrator()
    return {"scenarios": orch.list_scenarios()}


@app.post("/api/game/create")
async def game_create(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    num_characters: int | None = Form(None, ge=3, le=12),
    enabled_skills: str | None = Form(None),
):
    """Create a new game session from an uploaded document or text.

    enabled_skills: Optional comma-separated list of skill IDs to activate.
                    If not provided, all skills are enabled by default.
    """
    orch = _require_orchestrator()
    try:
        skill_list = None
        if enabled_skills is not None:
            skill_list = [s.strip() for s in enabled_skills.split(",") if s.strip()]

        if file:
            file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
            if len(file_bytes) > MAX_UPLOAD_BYTES:
                return JSONResponse(status_code=413, content={"error": "File too large (max 10MB)"})
            result = await orch.create_session_from_file(
                file_bytes, file.filename or "upload.pdf", num_characters,
                enabled_skills=skill_list,
            )
        elif text:
            result = await orch.create_session_from_text(
                text, num_characters, enabled_skills=skill_list,
            )
        else:
            # Default: create with fallback world
            result = await orch.create_session_from_text(
                "", num_characters, enabled_skills=skill_list,
            )

        # Register character voices with TTS
        if voice:
            voice_map = {c.id: c.voice_id for c in result.characters}
            voice.set_character_voices(voice_map)

        return result.model_dump()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/game/scenario/{scenario_id}")
async def game_load_scenario(
    scenario_id: str,
    num_characters: int | None = Query(None, ge=3, le=12),
    enabled_skills: str | None = Query(None),
):
    """Create a new game session from a pre-built scenario."""
    orch = _require_orchestrator()
    try:
        skill_list = None
        if enabled_skills is not None:
            skill_list = [s.strip() for s in enabled_skills.split(",") if s.strip()]

        result = await orch.create_session_from_scenario(
            scenario_id, num_characters, enabled_skills=skill_list,
        )
        if voice:
            voice_map = {c.id: c.voice_id for c in result.characters}
            voice.set_character_voices(voice_map)
        return result.model_dump()
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/game/{session_id}/state")
async def game_state_endpoint(session_id: str, full: bool = Query(False)):
    """Get the public game state (no hidden info)."""
    orch = _require_orchestrator()
    try:
        return await orch.get_public_state(session_id, full=full)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})


@app.post("/api/game/{session_id}/start")
async def game_start(session_id: str):
    """Transition from lobby to discussion phase."""
    orch = _require_orchestrator()
    try:
        return await orch.start_game(session_id)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/api/game/{session_id}/open-discussion")
async def game_open_discussion(session_id: str):
    """Trigger opening statements from AI characters at the start of discussion."""
    orch = _require_orchestrator()
    async def event_stream():
        try:
            async for event in orch.handle_open_discussion(session_id):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from %s SSE stream", "open-discussion")
            raise
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@app.post("/api/game/{session_id}/chat")
async def game_chat(session_id: str, request: GameChatRequest):
    """Player sends a message; AI characters respond via SSE."""
    orch = _require_orchestrator()
    async def event_stream():
        try:
            async for event in orch.handle_chat(
                session_id, request.message, request.target_character_id
            ):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from %s SSE stream", "chat")
            raise
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@app.post("/api/game/{session_id}/vote")
async def game_vote(session_id: str, request: GameVoteRequest):
    """Cast a vote and stream the voting results via SSE."""
    orch = _require_orchestrator()
    async def event_stream():
        try:
            async for event in orch.handle_vote(
                session_id, request.target_character_id
            ):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from %s SSE stream", "vote")
            raise
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@app.post("/api/game/{session_id}/night")
async def game_night(session_id: str):
    """Trigger night phase. Streams SSE events for night actions and results."""
    orch = _require_orchestrator()
    async def event_stream():
        try:
            async for event in orch.handle_night(session_id):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from %s SSE stream", "night")
            raise
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


class TTSStreamRequest(BaseModel):
    text: str
    voice_id: str = "Sarah"


@app.post("/api/voice/tts/stream")
async def voice_tts_stream(request: TTSStreamRequest):
    """Stream TTS audio as chunks."""
    if not voice or not voice.available:
        return JSONResponse(
            status_code=503,
            content={"error": "Voice not available"},
        )

    async def audio_stream():
        try:
            async for chunk in voice.stream_tts(request.text, request.voice_id):
                yield chunk
        except Exception as e:
            logger.warning("TTS stream error: %s", e)
            return

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")


class SFXRequest(BaseModel):
    prompt: str
    duration_seconds: float = 3.0


@app.post("/api/voice/sfx")
async def generate_sfx(request: SFXRequest):
    """Generate sound effects using ElevenLabs SFX API."""
    if not voice or not voice.available:
        return JSONResponse(
            status_code=503,
            content={"error": "Voice not available"},
        )

    audio = await voice.generate_sfx(request.prompt, request.duration_seconds)
    if audio:
        return Response(content=audio, media_type="audio/mpeg")
    return JSONResponse(
        status_code=502,
        content={"error": "SFX generation failed"},
    )


@app.get("/api/game/{session_id}/player-role")
async def get_player_role(session_id: str):
    """Get the player's hidden role (only visible to the player)."""
    orch = _require_orchestrator()
    try:
        return await orch.get_player_role(session_id)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})


@app.post("/api/game/{session_id}/night-chat")
async def night_chat(session_id: str, request: GameChatRequest):
    """Player sends a night whisper to evil allies. AI allies respond via SSE."""
    orch = _require_orchestrator()
    async def event_stream():
        try:
            async for event in orch.handle_night_chat(session_id, request.message):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from %s SSE stream", "night-chat")
            raise
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@app.post("/api/game/{session_id}/night-action")
async def player_night_action(session_id: str, request: PlayerNightActionRequest):
    """Submit the player's night action. Returns SSE stream with night results."""
    orch = _require_orchestrator()
    async def event_stream():
        try:
            async for event in orch.handle_player_night_action(
                session_id, request.action_type, request.target_character_id
            ):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from %s SSE stream", "night-action")
            raise
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@app.get("/api/game/{session_id}/reveal/{character_id}")
async def game_reveal(session_id: str, character_id: str):
    """Get an eliminated character's hidden role info."""
    orch = _require_orchestrator()
    try:
        return await orch.get_reveal(session_id, character_id)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return JSONResponse(status_code=404, content={"error": msg})
        return JSONResponse(status_code=400, content={"error": msg})
