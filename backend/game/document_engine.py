"""Document-to-WorldModel pipeline using Mistral OCR 3 + Large 3."""

import os
import json
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

from backend.models.game_models import WorldModel
from backend.game.prompts import WORLD_EXTRACTION_SYSTEM, WORLD_EXTRACTION_USER

load_dotenv()

SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent / "test" / "scenarios"


class DocumentEngine:
    def __init__(self):
        self._mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    async def process_document(self, file_bytes: bytes, filename: str) -> WorldModel:
        """Full pipeline: OCR -> extract world model."""
        try:
            text = await self._ocr_extract(file_bytes, filename)
        except Exception:
            try:
                text = file_bytes.decode("utf-8")
            except Exception:
                return self._fallback_world()
        return await self._extract_world_model(text)

    async def process_text(self, text: str) -> WorldModel:
        """Direct text to world model (skip OCR)."""
        if not text.strip():
            return self._fallback_world()
        return await self._extract_world_model(text)

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
        uploaded = await self._mistral.files.upload_async(
            file={"file_name": filename, "content": file_bytes},
            purpose="ocr",
        )
        signed = await self._mistral.files.get_signed_url_async(file_id=uploaded.id)
        result = await self._mistral.ocr.process_async(
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": signed.url},
        )
        pages = []
        for page in result.pages:
            pages.append(page.markdown)
        return "\n\n".join(pages)

    async def _extract_world_model(self, text: str) -> WorldModel:
        """Use Mistral Large 3 to extract world model from text."""
        try:
            response = await self._mistral.chat.complete_async(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": WORLD_EXTRACTION_SYSTEM},
                    {"role": "user", "content": WORLD_EXTRACTION_USER.format(text=text[:8000])},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return WorldModel.model_validate(data)
        except Exception:
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
        )
