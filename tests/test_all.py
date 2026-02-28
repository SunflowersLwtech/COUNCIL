"""COUNCIL — Comprehensive automated test suite.

Tests:
  1. API connectivity (Mistral Large 3, Devstral 2, ElevenLabs)
  2. Agent unit tests (Architecture, Code Quality, Documentation, Security)
     — Each returns structured AgentReport
  3. Integration test (end-to-end pipeline → ConsensusSummary)
  4. Voice middleware test (TTS generation)

Usage:
    cd mistral-hackathon
    python -m tests.test_all
"""

import os
import sys
import asyncio
import time
import traceback
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

DEMO_PATH = PROJECT_ROOT / "demo" / "sample_project"

# ── Helpers ──────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"

results: list[tuple[str, str, str]] = []  # (test_name, status, detail)


def record(name: str, status: str, detail: str = ""):
    results.append((name, status, detail))
    tag = PASS if status == "PASS" else (FAIL if status == "FAIL" else SKIP)
    print(f"  [{tag}] {name}")
    if detail and status == "FAIL":
        for line in detail.strip().split("\n"):
            print(f"         {line}")


def print_summary():
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    skipped = sum(1 for _, s, _ in results if s == "SKIP")
    total = len(results)
    print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}")
    if failed:
        print(f"\n  Failed tests:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f"    - {name}: {detail[:120]}")
    print("=" * 60)
    return failed == 0


# ── Collect demo files (reuse run.py logic) ──────────────────────────

def collect_demo_files() -> dict[str, str]:
    from run import collect_files
    return collect_files(DEMO_PATH)


# ═════════════════════════════════════════════════════════════════════
#  TEST 1: API Connectivity
# ═════════════════════════════════════════════════════════════════════

async def test_mistral_large():
    """Test Mistral Large 3 API connectivity."""
    from mistralai import Mistral
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    response = await client.chat.complete_async(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": "Reply with exactly: HELLO_COUNCIL"}],
        temperature=0.0,
    )
    text = response.choices[0].message.content
    assert "HELLO_COUNCIL" in text, f"Unexpected response: {text[:100]}"
    return text.strip()


async def test_devstral():
    """Test Devstral 2 API connectivity."""
    from mistralai import Mistral
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    response = await client.chat.complete_async(
        model="devstral-latest",
        messages=[{"role": "user", "content": "Reply with exactly: DEVSTRAL_OK"}],
        temperature=0.0,
    )
    text = response.choices[0].message.content
    assert "DEVSTRAL_OK" in text, f"Unexpected response: {text[:100]}"
    return text.strip()


async def test_elevenlabs_connectivity():
    """Test ElevenLabs API connectivity by listing voices."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return "NO_KEY"
    from elevenlabs import ElevenLabs
    client = ElevenLabs(api_key=api_key)
    voices = await asyncio.to_thread(client.voices.get_all)
    assert len(voices.voices) > 0, "No voices returned"
    return f"{len(voices.voices)} voices available"


# ═════════════════════════════════════════════════════════════════════
#  TEST 2: Agent Unit Tests — Structured Output (AgentReport)
# ═════════════════════════════════════════════════════════════════════

async def test_architecture_agent():
    """Test ArchitectureAgent returns structured AgentReport."""
    from backend.agents.architecture_agent import ArchitectureAgent
    from backend.models.findings import AgentReport
    agent = ArchitectureAgent()
    files = collect_demo_files()
    file_list = list(files.keys())
    result = await agent.analyze_files(file_list, files)
    assert isinstance(result, AgentReport), f"Expected AgentReport, got {type(result)}"
    assert result.agent_role, "Missing agent_role"
    assert len(result.findings) > 0, "No findings returned"
    assert result.summary, "Missing summary"
    return f"{len(result.findings)} findings, role={result.agent_role}"


async def test_code_quality_agent():
    """Test CodeQualityAgent returns structured AgentReport (Devstral 2)."""
    from backend.agents.code_quality_agent import CodeQualityAgent
    from backend.models.findings import AgentReport
    agent = CodeQualityAgent()
    files = collect_demo_files()
    file_list = list(files.keys())
    result = await agent.analyze_files(file_list, files)
    assert isinstance(result, AgentReport), f"Expected AgentReport, got {type(result)}"
    assert len(result.findings) > 0, "No findings returned"
    assert result.summary, "Missing summary"
    return f"{len(result.findings)} findings, role={result.agent_role}"


async def test_documentation_agent():
    """Test DocumentationAgent returns structured AgentReport."""
    from backend.agents.documentation_agent import DocumentationAgent
    from backend.models.findings import AgentReport
    agent = DocumentationAgent()
    files = collect_demo_files()
    file_list = list(files.keys())
    result = await agent.analyze_files(file_list, files)
    assert isinstance(result, AgentReport), f"Expected AgentReport, got {type(result)}"
    assert len(result.findings) > 0, "No findings returned"
    assert result.summary, "Missing summary"
    return f"{len(result.findings)} findings, role={result.agent_role}"


async def test_security_agent():
    """Test SecurityAgent: static scan + structured AgentReport."""
    from backend.agents.security_agent import SecurityAgent
    from backend.models.findings import AgentReport
    agent = SecurityAgent()
    files = collect_demo_files()
    file_list = list(files.keys())

    # Sub-test A: Static scan should detect hardcoded secrets
    static_findings = agent._static_scan(files)
    assert len(static_findings) > 0, "Static scan found no secrets in demo project!"
    has_secret = any(
        "secret" in f.lower() or "password" in f.lower() or "database" in f.lower()
        for f in static_findings
    )
    assert has_secret, f"Static scan missed hardcoded secrets: {static_findings}"

    # Sub-test B: Full LLM analysis with structured output
    result = await agent.analyze_files(file_list, files)
    assert isinstance(result, AgentReport), f"Expected AgentReport, got {type(result)}"
    assert len(result.findings) > 0, "No findings returned"
    # Should have at least one critical or high severity finding
    severities = {f.severity for f in result.findings}
    assert severities & {"critical", "high"}, f"Expected critical/high findings, got {severities}"

    return f"Static: {len(static_findings)}, Structured: {len(result.findings)} findings"


# ═════════════════════════════════════════════════════════════════════
#  TEST 3: Integration — End-to-end pipeline → ConsensusSummary
# ═════════════════════════════════════════════════════════════════════

async def test_e2e_pipeline():
    """Run full pipeline (Ingest → Scan → Align) → ConsensusSummary."""
    from backend.orchestrator import Orchestrator
    from backend.models.findings import ConsensusSummary
    from run import collect_files

    # Phase 1: Ingest
    file_contents = collect_files(DEMO_PATH)
    assert len(file_contents) > 0, "No files collected from demo project"

    # Full pipeline
    orch = Orchestrator()
    consensus = await orch.run_pipeline(file_contents)

    assert isinstance(consensus, ConsensusSummary), f"Expected ConsensusSummary, got {type(consensus)}"
    assert consensus.executive_summary, "Missing executive summary"

    # Should have found issues across severity levels
    total = (
        len(consensus.critical) + len(consensus.high)
        + len(consensus.medium) + len(consensus.low)
    )
    assert total > 0, "No findings in consensus"

    # All 4 agents should have reported
    assert len(orch.scan_results) == 4, f"Expected 4 agents, got {len(orch.scan_results)}"

    return (
        f"4 agents, {total} findings "
        f"({len(consensus.critical)}C/{len(consensus.high)}H/"
        f"{len(consensus.medium)}M/{len(consensus.low)}L), "
        f"summary: {len(consensus.executive_summary)} chars"
    )


# ═════════════════════════════════════════════════════════════════════
#  TEST 4: Voice Middleware
# ═════════════════════════════════════════════════════════════════════

async def test_voice_init():
    """Test VoiceMiddleware initialization."""
    from backend.voice.tts_middleware import VoiceMiddleware
    vm = VoiceMiddleware()
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if api_key:
        assert vm.available, "VoiceMiddleware should be available with API key"
        return "VoiceMiddleware initialized with ElevenLabs client"
    else:
        assert not vm.available, "VoiceMiddleware should not be available without key"
        return "VoiceMiddleware initialized (no key, correctly unavailable)"


async def test_voice_tts():
    """Test TTS: generate a short audio clip."""
    from backend.voice.tts_middleware import VoiceMiddleware
    vm = VoiceMiddleware()
    if not vm.available:
        return "NO_KEY"

    audio = await vm.text_to_speech("COUNCIL analysis complete.", "orchestrator")
    assert audio is not None, "TTS returned None"
    assert len(audio) > 100, f"Audio too small: {len(audio)} bytes"
    # Check MP3 magic bytes (ID3 or 0xFF 0xFB)
    assert audio[:3] == b'ID3' or audio[:2] == b'\xff\xfb', "Not valid MP3 data"
    return f"Generated {len(audio)} bytes of MP3 audio"


# ═════════════════════════════════════════════════════════════════════
#  Runner
# ═════════════════════════════════════════════════════════════════════

async def run_test(name: str, coro_func):
    """Run a single async test and record result."""
    try:
        t0 = time.time()
        detail = await coro_func()
        elapsed = time.time() - t0
        if detail == "NO_KEY":
            record(name, "SKIP", "API key not configured")
        else:
            record(name, "PASS", f"({elapsed:.1f}s) {detail}")
    except Exception as e:
        record(name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()[-300:]}")


async def main():
    print("=" * 60)
    print("  COUNCIL — Automated Test Suite")
    print("=" * 60)
    print()

    # ── Test 1: API Connectivity ──
    print("[Test 1] API Connectivity")
    await run_test("Mistral Large 3 API", test_mistral_large)
    await run_test("Devstral 2 API", test_devstral)
    await run_test("ElevenLabs API", test_elevenlabs_connectivity)
    print()

    # ── Test 2: Agent Unit Tests (Structured Output) ──
    print("[Test 2] Agent Unit Tests (AgentReport)")
    await run_test("Architecture Agent", test_architecture_agent)
    await run_test("Code Quality Agent (Devstral 2)", test_code_quality_agent)
    await run_test("Documentation Agent", test_documentation_agent)
    await run_test("Security Agent (static + structured)", test_security_agent)
    print()

    # ── Test 3: Integration (E2E Pipeline → ConsensusSummary) ──
    print("[Test 3] Integration — End-to-End Pipeline")
    await run_test("E2E Pipeline → ConsensusSummary", test_e2e_pipeline)
    print()

    # ── Test 4: Voice Middleware ──
    print("[Test 4] Voice Middleware")
    await run_test("VoiceMiddleware init", test_voice_init)
    await run_test("TTS Audio Generation", test_voice_tts)
    print()

    # ── Summary ──
    all_passed = print_summary()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
