"""Document-to-WorldModel pipeline using Mistral OCR 3 + Large 3."""

import asyncio
import os
import json
import logging
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

from backend.models.game_models import WorldModel
from backend.game.prompts import WORLD_EXTRACTION_SYSTEM, WORLD_EXTRACTION_USER

load_dotenv()
logger = logging.getLogger(__name__)

SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent / "test" / "scenarios"

# Timeout for Mistral API calls (seconds)
_MISTRAL_TIMEOUT = 60

# Adaptive document size limits
_TEXT_LIMIT = 20_000          # Plain text upper bound
_OCR_DIRECT_LIMIT = 50_000   # OCR docs used directly up to this
_OCR_CHUNK_THRESHOLD = 120_000  # Above this, use hierarchical extraction
_CHUNK_SIZE = 30_000          # Chunk size for hierarchical extraction


def _new_mistral_client() -> Mistral:
    """Create a fresh Mistral client to avoid stale httpx connection pools."""
    return Mistral(api_key=os.environ["MISTRAL_API_KEY"])


class DocumentEngine:
    def __init__(self):
        pass  # No longer reuse a single Mistral client

    async def process_document(self, file_bytes: bytes, filename: str) -> WorldModel:
        """Full pipeline: OCR -> extract world model with adaptive sizing."""
        try:
            text = await self._ocr_extract(file_bytes, filename)
        except Exception:
            try:
                text = file_bytes.decode("utf-8")
            except Exception:
                return self._fallback_world()

        total_chars = len(text)
        logger.info("Document extracted: %d chars from %s", total_chars, filename)

        if total_chars <= _OCR_DIRECT_LIMIT:
            return await self._extract_world_model(text)
        elif total_chars <= _OCR_CHUNK_THRESHOLD:
            logger.warning("Document truncated from %d to %d chars", total_chars, _OCR_DIRECT_LIMIT)
            return await self._extract_world_model(text[:_OCR_DIRECT_LIMIT])
        else:
            return await self._hierarchical_extract(text)

    async def process_text(self, text: str) -> WorldModel:
        """Direct text to world model (skip OCR) with adaptive sizing."""
        if not text.strip():
            return self._fallback_world()
        return await self._extract_world_model(text[:_TEXT_LIMIT])

    async def load_scenario(self, scenario_id: str) -> WorldModel:
        """Load a pre-built test scenario."""
        scenarios = self.list_scenarios()
        for s in scenarios:
            if s["id"] == scenario_id:
                text = Path(s["path"]).read_text(encoding="utf-8")
                return await self._extract_world_model(text)
        raise ValueError(f"Scenario {scenario_id} not found")

    def list_scenarios(self) -> list[dict]:
        """List available test scenarios."""
        scenarios = []
        if SCENARIOS_DIR.exists():
            for f in sorted(SCENARIOS_DIR.glob("*.md")):
                sid = f.stem
                scenarios.append({
                    "id": sid,
                    "name": f.stem.replace("-", " ").title(),
                    "path": str(f),
                })
        return scenarios

    async def _ocr_extract(self, file_bytes: bytes, filename: str) -> str:
        """Use Mistral OCR to extract text from document."""
        client = _new_mistral_client()
        uploaded = await asyncio.wait_for(
            client.files.upload_async(
                file={"file_name": filename, "content": file_bytes},
                purpose="ocr",
            ),
            timeout=_MISTRAL_TIMEOUT,
        )
        try:
            signed = await asyncio.wait_for(
                client.files.get_signed_url_async(file_id=uploaded.id),
                timeout=_MISTRAL_TIMEOUT,
            )
            result = await asyncio.wait_for(
                client.ocr.process_async(
                    model="mistral-ocr-latest",
                    document={"type": "document_url", "document_url": signed.url},
                ),
                timeout=_MISTRAL_TIMEOUT,
            )
            pages = []
            for page in result.pages:
                pages.append(page.markdown)
            return "\n\n".join(pages)
        finally:
            try:
                await client.files.delete_async(file_id=uploaded.id)
            except Exception:
                logger.warning("Failed to clean up uploaded file %s", uploaded.id)

    async def _hierarchical_extract(self, text: str) -> WorldModel:
        """Two-pass extraction for very large documents."""
        chunks = [text[i:i + _CHUNK_SIZE] for i in range(0, len(text), _CHUNK_SIZE)]
        logger.info("Hierarchical extraction: %d chunks of ~%d chars", len(chunks), _CHUNK_SIZE)

        async def summarize_chunk(chunk: str) -> str:
            def _sync():
                client = _new_mistral_client()
                resp = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {"role": "system", "content": "Extract key game elements: factions, roles, rules, win conditions, setting details. Be concise."},
                        {"role": "user", "content": f"Summarize game-relevant content from this section:\n\n{chunk}"},
                    ],
                    temperature=0.1,
                )
                return resp.choices[0].message.content
            try:
                return await asyncio.wait_for(asyncio.to_thread(_sync), timeout=30)
            except Exception:
                return ""

        summaries = await asyncio.gather(
            *[summarize_chunk(c) for c in chunks],
            return_exceptions=True,
        )
        combined = "\n\n---\n\n".join(
            s for s in summaries if isinstance(s, str) and s.strip()
        )
        return await self._extract_world_model(combined[:_OCR_DIRECT_LIMIT])

    async def _extract_world_model(self, text: str) -> WorldModel:
        """Use Mistral Large 3 to extract world model from text."""
        try:
            logger.info("Calling Mistral API for world extraction (%d chars)...", len(text))
            prompt_text = text

            def _sync_extract():
                """Run Mistral call in a thread to avoid uvicorn event loop issues."""
                client = _new_mistral_client()
                return client.chat.complete(
                    model="mistral-large-latest",
                    messages=[
                        {"role": "system", "content": WORLD_EXTRACTION_SYSTEM},
                        {"role": "user", "content": WORLD_EXTRACTION_USER.format(text=prompt_text)},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )

            response = await asyncio.wait_for(
                asyncio.to_thread(_sync_extract),
                timeout=_MISTRAL_TIMEOUT,
            )
            logger.info("World extraction API returned successfully")
            data = json.loads(response.choices[0].message.content)
            return WorldModel.model_validate(data)
        except asyncio.TimeoutError:
            logger.error("Mistral API timed out for world extraction, using fallback")
            return self._fallback_world()
        except Exception:
            logger.error("World extraction error, using fallback")
            return self._fallback_world()

    def _fallback_world(self) -> WorldModel:
        """Classic Werewolf fallback."""
        return WorldModel(
            title="Classic Werewolf",
            setting="A quiet village where werewolves hide among the villagers.",
            factions=[
                {"name": "Village", "alignment": "good", "description": "Innocent villagers trying to find the werewolves"},
                {"name": "Werewolf", "alignment": "evil", "description": "Werewolves hiding among the villagers"},
            ],
            roles=[
                {"name": "Villager", "faction": "Village", "ability": "None", "description": "A regular villager with keen observation skills"},
                {"name": "Seer", "faction": "Village", "ability": "Can sense evil", "description": "A mystic who can detect werewolves"},
                {"name": "Werewolf", "faction": "Werewolf", "ability": "Deception", "description": "A werewolf disguised as a villager"},
            ],
            win_conditions=[
                {"faction": "Village", "condition": "Eliminate all werewolves"},
                {"faction": "Werewolf", "condition": "Equal or outnumber the villagers"},
            ],
            phases=[
                {"name": "Discussion", "duration": "5 minutes", "description": "Open discussion among all players"},
                {"name": "Voting", "duration": "2 minutes", "description": "Vote to eliminate a suspect"},
                {"name": "Reveal", "duration": "1 minute", "description": "Reveal the eliminated player's true role"},
            ],
            flavor_text="The moon is full tonight. Someone at this table is not who they claim to be...",
            recommended_player_count=6,
        )
