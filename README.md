# COUNCIL — AI Social Deduction Game

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Next.js 15](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-FF7000?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiPjwvc3ZnPg==&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-green)

**COUNCIL** transforms any story, document, or scenario into a fully playable social deduction game powered by Mistral AI. Autonomous characters with distinct personalities debate, deceive, form alliances, and vote to eliminate each other — while you play alongside them as a hidden role.

---

## Key Features

- **Document-to-Game Engine** — Upload a PDF, paste text, or pick a built-in scenario. Mistral AI generates the world, factions, roles, and win conditions automatically.
- **Autonomous AI Characters** — Each character has a unique personality (Big Five, MBTI, Sims-style traits), emotional state, relationships, and memory that evolve throughout the game.
- **Hidden Role Gameplay** — Players receive a secret faction and role (Werewolf, Seer, Doctor, Villager, etc.) with unique night actions and win conditions.
- **Multi-Phase Game Loop** — Discussion, Voting, Night, and Reveal phases with full AI orchestration and narrative pacing.
- **Modular Skills System** — YAML-defined cognitive skills (strategic reasoning, deception mastery, memory consolidation) are injected into agent prompts at runtime.
- **Voice Integration** — ElevenLabs TTS/STT for character speech and player voice input with per-character voice mapping.
- **Real-Time Streaming** — Server-Sent Events (SSE) stream AI dialogue, votes, and night results to the frontend in real time.
- **Session Persistence** — Redis (Upstash) stores game state and agent memory for recovery; Supabase for long-term data.
- **Tension & Pacing** — Dynamic tension tracking triggers game events (complications, revelations, betrayals) to keep sessions engaging.

---

## Game Flow

1. **Create** — Upload a document, paste story text, or select a built-in scenario. Configure the number of characters and which skills to activate.
2. **Lobby** — Review the generated world setting, character roster, and your secret role assignment before starting.
3. **Discussion** — Chat with AI characters who respond in-character with personality-driven dialogue. Characters react spontaneously, form opinions, and track suspicion.
4. **Voting** — All players (human + AI) cast elimination votes. The character with the most votes is eliminated and their hidden role is revealed.
5. **Night** — Hidden roles perform faction-specific actions: Werewolves kill, Seers investigate, Doctors protect. The player submits their own night action.
6. **Repeat** — The game cycles through Discussion, Voting, and Night phases until a faction achieves its win condition.

---

## Architecture

```
                   +------------------+
                   |   Next.js 15     |
                   |   Frontend       |
                   |  (React + Three) |
                   +--------+---------+
                            |
                       SSE / REST
                            |
                   +--------v---------+
                   |   FastAPI         |
                   |   Backend         |
                   +--------+---------+
                            |
          +-----------------+-----------------+
          |                 |                 |
  +-------v------+  +------v-------+  +------v-------+
  |  Game         |  |  Character   |  |  Voice       |
  |  Orchestrator |  |  Agents      |  |  Middleware   |
  +-------+------+  +------+-------+  +--------------+
          |                 |                 |
  +-------v------+  +------v-------+  +------v-------+
  |  Game Master  |  |  Skill       |  |  ElevenLabs  |
  |  (Narration)  |  |  Loader      |  |  TTS / STT   |
  +--------------+  +--------------+  +--------------+
          |
  +-------v------+
  |  Persistence  |
  |  Redis +      |
  |  Supabase     |
  +--------------+
          |
  +-------v------+
  |  Mistral AI   |
  |  LLM API      |
  +--------------+
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | Mistral AI SDK | Character dialogue, world generation, structured output |
| Backend | Python 3.12 + FastAPI | REST API, SSE streaming, game orchestration |
| Frontend | Next.js 15 + React 19 | Game UI, 3D scene rendering |
| 3D Rendering | Three.js + React Three Fiber | Character avatars and scene visualization |
| Styling | Tailwind CSS 4 | UI styling |
| Voice | ElevenLabs | Text-to-Speech, Speech-to-Text |
| Structured Output | Pydantic v2 | LLM response validation and type safety |
| Persistence | Redis (Upstash) | Game state and agent memory caching |
| Database | Supabase | Long-term session and analytics storage |
| Streaming | Server-Sent Events | Real-time game event delivery |

---

## Quick Start

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/) (Miniconda or Anaconda)
- [Node.js](https://nodejs.org/) 18+
- API keys: [Mistral AI](https://console.mistral.ai/), [ElevenLabs](https://elevenlabs.io/) (optional for voice)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/COUNCIL.git
cd COUNCIL
```

### 2. Set up the conda environment

```bash
conda create -n council python=3.12 -y
conda activate council
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
MISTRAL_API_KEY=your_mistral_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key   # optional
SUPABASE_URL=https://your-project.supabase.co # optional
SUPABASE_ANON_KEY=your_key                    # optional
```

### 6. Run the application

**Terminal 1 — Backend:**

```bash
conda activate council
python run.py
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to start playing.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/skills` | GET | List available agent skills |
| `/api/game/scenarios` | GET | List built-in scenarios |
| `/api/game/create` | POST | Create game from uploaded file or pasted text |
| `/api/game/scenario/{id}` | POST | Create game from a built-in scenario |
| `/api/game/{id}/start` | POST | Transition from lobby to discussion phase |
| `/api/game/{id}/state` | GET | Fetch current game state (public or full) |
| `/api/game/{id}/chat` | POST | Send message; AI characters respond via SSE |
| `/api/game/{id}/vote` | POST | Cast vote; streams voting results via SSE |
| `/api/game/{id}/night` | POST | Trigger night phase; streams night actions via SSE |
| `/api/game/{id}/player-role` | GET | Get the player's hidden role |
| `/api/game/{id}/night-action` | POST | Submit player night action |
| `/api/game/{id}/reveal/{char}` | GET | Get eliminated character's hidden role |
| `/api/voice/tts` | POST | Generate character TTS audio |
| `/api/voice/tts/stream` | POST | Stream TTS audio in chunks |
| `/api/voice/sfx` | POST | Generate sound effects |
| `/api/voice/scribe-token` | POST | Mint single-use STT token |

---

## Project Structure

```
COUNCIL/
├── backend/
│   ├── server.py                 # FastAPI app and all API routes
│   ├── game/
│   │   ├── orchestrator.py       # Session management and phase coordination
│   │   ├── game_master.py        # Narrative generation and tension pacing
│   │   ├── character_agent.py    # Personality-driven AI character engine
│   │   ├── character_factory.py  # LLM-powered character generation
│   │   ├── document_engine.py    # Document/text to world model conversion
│   │   ├── skill_loader.py       # YAML skill discovery and injection
│   │   ├── persistence.py        # Redis + Supabase state persistence
│   │   ├── state.py              # State helpers and serialization
│   │   ├── prompts.py            # Prompt templates for LLM calls
│   │   ├── adversarial_tester.py # Automated gameplay testing
│   │   └── skills/               # YAML skill definitions
│   │       ├── strategic_reasoning.yaml
│   │       ├── deception_mastery.yaml
│   │       ├── memory_consolidation.yaml
│   │       ├── social_evaluation.yaml
│   │       ├── goal_driven_behavior.yaml
│   │       ├── discussion_dynamics.yaml
│   │       └── contrastive_examples.yaml
│   ├── agents/
│   │   └── base_agent.py         # Mistral agent base class
│   ├── models/
│   │   └── game_models.py        # Pydantic v2 data models
│   └── voice/
│       └── tts_middleware.py     # ElevenLabs TTS/STT integration
├── frontend/
│   ├── app/                      # Next.js App Router (layout, page)
│   ├── components/               # React UI components
│   │   ├── GameBoard.tsx         # Main game interface
│   │   ├── chat.tsx              # Chat panel
│   │   ├── VotePanel.tsx         # Voting interface
│   │   ├── NightActionPanel.tsx  # Night action selection
│   │   ├── PlayerRoleCard.tsx    # Player's secret role display
│   │   ├── CharacterCard.tsx     # Character info cards
│   │   ├── CharacterReveal.tsx   # Elimination reveal animation
│   │   ├── DocumentUpload.tsx    # File/text upload form
│   │   ├── GameLobby.tsx         # Pre-game lobby
│   │   ├── GhostOverlay.tsx      # Eliminated player ghost effect
│   │   ├── PhaseIndicator.tsx    # Current phase display
│   │   └── scene/                # Three.js 3D scene components
│   ├── hooks/                    # React hooks (game state, voice)
│   └── lib/                      # API client and utilities
├── tests/                        # Unit and integration tests
├── e2e/                          # End-to-end tests
├── docs/                         # Documentation
├── run.py                        # Backend server launcher
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variable template
```

---

## Skills System

COUNCIL uses a modular **Skills System** to enhance AI character behavior. Skills are defined as YAML files in `backend/game/skills/` and are injected into agent prompts at runtime.

Each skill specifies:
- **Targets** — Which prompt contexts to inject into (e.g., `character_agent`, `vote_prompt`, `night_action`)
- **Priority** — Execution order (lower = earlier)
- **Injections** — Prompt fragments appended to agent system prompts
- **Dependencies / Conflicts** — Skill compatibility rules

Available skills include: Strategic Reasoning, Deception Mastery, Memory Consolidation, Social Evaluation, Goal-Driven Behavior, Discussion Dynamics, and Contrastive Examples.

Skills can be toggled per game session via the `enabled_skills` parameter when creating a game.

---

## Testing

```bash
conda activate council
pytest -q
```

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments

Built for the **Mistral AI Worldwide Hackathon 2026**.

Powered by [Mistral AI](https://mistral.ai/) and [ElevenLabs](https://elevenlabs.io/).
