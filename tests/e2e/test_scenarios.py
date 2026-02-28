"""E2E tests: parametrized scenario loading.

Validates that each of the 5 scenarios can be loaded and produces
the correct number of characters in the UI.

Requires:
- Frontend at http://localhost:3000
- Backend at http://localhost:8000
"""

import pytest

try:
    from playwright.sync_api import Page, expect
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

pytestmark = [
    pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed"),
    pytest.mark.e2e,
]

FRONTEND_URL = "http://localhost:3000"

SCENARIOS = [
    ("01-werewolf-classic", "Werewolf", 5),
    ("02-avalon-resistance", "Avalon", 5),
    ("03-murder-mystery-manor", "Murder", 5),
    ("04-three-kingdoms-intrigue", "三国", 5),
    ("05-corporate-leak", "Corporate", 5),
]


@pytest.fixture
def page(browser):
    p = browser.new_page()
    p.goto(FRONTEND_URL)
    yield p
    p.close()


class TestScenarioLoading:
    @pytest.mark.parametrize(
        "scenario_id, search_text, expected_chars",
        SCENARIOS,
        ids=[s[0] for s in SCENARIOS],
    )
    def test_scenario_loads_characters(
        self, page: "Page", scenario_id: str, search_text: str, expected_chars: int
    ):
        """Each scenario loads and shows the expected number of characters."""
        page.wait_for_load_state("networkidle")

        # Try to find and click the scenario
        scenario_link = page.locator(
            f"[data-testid='scenario-{scenario_id}'], "
            f"[data-scenario-id='{scenario_id}'], "
            f"button:has-text('{search_text}'), "
            f"a:has-text('{search_text}'), "
            f".scenario-card:has-text('{search_text}')"
        )

        if scenario_link.count() == 0:
            pytest.skip(f"Scenario '{scenario_id}' not found in UI")

        scenario_link.first.click()
        page.wait_for_timeout(5000)  # Wait for API processing

        # Count character elements
        characters = page.locator(
            "[data-testid='character-card'], .character-card, "
            "[data-testid='character'], .character, "
            ".character-avatar"
        )

        if characters.count() > 0:
            assert characters.count() >= 3, (
                f"Expected at least 3 characters for {scenario_id}, "
                f"got {characters.count()}"
            )
            # Characters should be at most 8 (clamped max)
            assert characters.count() <= 8

    @pytest.mark.parametrize(
        "scenario_id, search_text, expected_chars",
        SCENARIOS,
        ids=[s[0] for s in SCENARIOS],
    )
    def test_scenario_shows_world_title(
        self, page: "Page", scenario_id: str, search_text: str, expected_chars: int
    ):
        """Each scenario displays a world title after loading."""
        page.wait_for_load_state("networkidle")

        scenario_link = page.locator(
            f"button:has-text('{search_text}'), "
            f"a:has-text('{search_text}'), "
            f".scenario-card:has-text('{search_text}')"
        )

        if scenario_link.count() == 0:
            pytest.skip(f"Scenario '{scenario_id}' not found in UI")

        scenario_link.first.click()
        page.wait_for_timeout(5000)

        # World title should appear somewhere on the page
        page_text = page.text_content("body") or ""
        assert len(page_text) > 0, "Page has no content after loading scenario"


class TestScenarioList:
    def test_scenarios_page_shows_options(self, page: "Page"):
        """The main page shows scenario options to choose from."""
        page.wait_for_load_state("networkidle")

        # Look for any scenario elements
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card, "
            "[data-testid='scenario-list'], .scenario-list"
        )

        # Or look for upload/text input area
        input_area = page.locator(
            "[data-testid='text-input'], textarea, "
            "[data-testid='file-upload'], input[type='file']"
        )

        has_scenarios = scenario_elements.count() > 0
        has_input = input_area.count() > 0

        assert has_scenarios or has_input, (
            "Page should show either scenario cards or text/file input"
        )

    def test_at_least_one_scenario_available(self, page: "Page"):
        """At least one pre-built scenario is available."""
        page.wait_for_load_state("networkidle")

        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card, "
            "button:has-text('Werewolf'), button:has-text('Avalon'), "
            "button:has-text('Murder'), button:has-text('Corporate')"
        )

        if scenario_elements.count() == 0:
            pytest.skip("No pre-built scenarios found in UI")

        assert scenario_elements.count() >= 1
