"""PersistenceManager — Redis (hot) + Supabase (cold) storage for game sessions."""

import os
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

TTL_SECONDS = 86400  # 24 hours


class PersistenceManager:
    """Gracefully degradable persistence layer.

    All public methods are wrapped in try/except — failures log warnings
    but never crash the game (falls back to in-memory only).
    """

    def __init__(self):
        self._redis = None
        self._supabase = None

    # ── Lifecycle ──────────────────────────────────────────────────────

    async def connect(self):
        """Initialise Redis and Supabase clients from env vars."""
        # Redis
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    redis_url, decode_responses=True, socket_timeout=5
                )
                await self._redis.ping()
                logger.info("Redis connected")
            except Exception as exc:
                logger.warning("Redis connection failed: %s", exc)
                self._redis = None
        else:
            logger.warning("REDIS_URL not set — persistence disabled")

        # Supabase
        sb_url = os.environ.get("SUPABASE_URL")
        sb_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if sb_url and sb_key:
            try:
                from supabase import create_client
                self._supabase = create_client(sb_url, sb_key)
                logger.info("Supabase connected")
            except Exception as exc:
                logger.warning("Supabase connection failed: %s", exc)
                self._supabase = None
        else:
            logger.warning("SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY not set — Supabase disabled")

    async def close(self):
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass

    @property
    def available(self) -> bool:
        return self._redis is not None

    # ── Redis operations ──────────────────────────────────────────────

    async def save_game_state(
        self, session_id: str, state_dict: dict, agent_memory: dict
    ):
        """Atomically write state + agent memory to Redis with TTL."""
        if not self._redis:
            return
        try:
            state_key = f"game:{session_id}:state"
            agents_key = f"game:{session_id}:agents"
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.set(state_key, json.dumps(state_dict), ex=TTL_SECONDS)
                pipe.set(agents_key, json.dumps(agent_memory), ex=TTL_SECONDS)
                await pipe.execute()
        except Exception as exc:
            logger.warning("Redis save failed for %s: %s", session_id, exc)

        # Fire-and-forget Supabase sync (non-blocking)
        asyncio.ensure_future(asyncio.to_thread(self._sync_to_supabase, session_id, state_dict))

    async def load_game_state(self, session_id: str) -> tuple[dict, dict] | None:
        """Load state + agent memory from Redis. Returns (state_dict, agent_memory) or None."""
        if not self._redis:
            return None
        try:
            state_key = f"game:{session_id}:state"
            agents_key = f"game:{session_id}:agents"
            state_raw, agents_raw = await self._redis.mget(state_key, agents_key)
            if not state_raw:
                return None
            state_dict = json.loads(state_raw)
            agent_memory = json.loads(agents_raw) if agents_raw else {}
            return state_dict, agent_memory
        except Exception as exc:
            logger.warning("Redis load failed for %s: %s", session_id, exc)
            return None

    async def delete_game_state(self, session_id: str):
        """Remove session from Redis and mark inactive in Supabase."""
        if self._redis:
            try:
                await self._redis.delete(
                    f"game:{session_id}:state",
                    f"game:{session_id}:agents",
                )
            except Exception as exc:
                logger.warning("Redis delete failed for %s: %s", session_id, exc)

        if self._supabase:
            try:
                await asyncio.to_thread(
                    lambda: self._supabase.table("game_sessions").update(
                        {"is_active": False, "updated_at": datetime.utcnow().isoformat()}
                    ).eq("session_id", session_id).execute()
                )
            except Exception as exc:
                logger.warning("Supabase deactivate failed for %s: %s", session_id, exc)

    async def session_exists(self, session_id: str) -> bool:
        """Quick check if session key exists in Redis."""
        if not self._redis:
            return False
        try:
            return bool(await self._redis.exists(f"game:{session_id}:state"))
        except Exception:
            return False

    # ── Supabase sync ─────────────────────────────────────────────────

    def _sync_to_supabase(self, session_id: str, state_dict: dict):
        """Upsert session index record to Supabase (fire-and-forget)."""
        if not self._supabase:
            return
        try:
            row = {
                "session_id": session_id,
                "world_title": state_dict.get("world", {}).get("title", ""),
                "phase": state_dict.get("phase", "lobby"),
                "round": state_dict.get("round", 1),
                "player_count": len(state_dict.get("characters", [])),
                "winner": state_dict.get("winner"),
                "is_active": state_dict.get("phase") != "ended",
                "active_skills": state_dict.get("active_skills", []),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._supabase.table("game_sessions").upsert(
                row, on_conflict="session_id"
            ).execute()
        except Exception as exc:
            logger.warning("Supabase sync failed for %s: %s", session_id, exc)
