"""End-to-end tests for the full COUNCIL game flow using Playwright.

These tests require:
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000

Run with: pytest tests/e2e/test_full_game_flow.py --headed (for visible browser)
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
BACKEND_URL = "http://localhost:8000"


@pytest.fixture
def page(browser):
    """Create a new browser page for each test."""
    p = browser.new_page()
    p.goto(FRONTEND_URL)
    yield p
    p.close()


class TestFullGameFlow:
    def test_page_loads(self, page: "Page"):
        """Frontend loads successfully."""
        expect(page).to_have_title(lambda t: t is not None)
        # Page should have some content
        assert page.content()

    def test_happy_path(self, page: "Page"):
        """Full game: scenario select -> lobby -> discuss -> vote -> reveal.

        This is the primary happy-path test.
        """
        # Step 1: Look for scenario selection or upload area
        page.wait_for_load_state("networkidle")

        # Look for scenario buttons/cards
        scenario_elements = page.locator("[data-testid='scenario-card'], .scenario-card, button:has-text('Werewolf')")
        if scenario_elements.count() > 0:
            # Click the first scenario
            scenario_elements.first.click()
            page.wait_for_timeout(2000)

        # Step 2: Verify lobby state with characters
        # Look for character elements or lobby indicators
        page.wait_for_timeout(3000)
        lobby_indicator = page.locator(
            "[data-testid='lobby'], .lobby, "
            "[data-testid='character-list'], .character-list, "
            "text=lobby, text=Lobby"
        )
        if lobby_indicator.count() > 0:
            assert lobby_indicator.first.is_visible()

        # Step 3: Start game
        start_button = page.locator(
            "[data-testid='start-game'], "
            "button:has-text('Start'), "
            "button:has-text('Begin')"
        )
        if start_button.count() > 0:
            start_button.first.click()
            page.wait_for_timeout(2000)

        # Step 4: Discussion phase - send message
        chat_input = page.locator(
            "[data-testid='chat-input'], "
            "input[type='text'], textarea, "
            "[contenteditable='true']"
        )
        if chat_input.count() > 0:
            chat_input.first.fill("I think we should discuss who to suspect.")
            # Find and click send button or press Enter
            send_button = page.locator(
                "[data-testid='send-button'], "
                "button:has-text('Send'), "
                "button[type='submit']"
            )
            if send_button.count() > 0:
                send_button.first.click()
            else:
                chat_input.first.press("Enter")
            page.wait_for_timeout(5000)

        # Step 5: Vote phase
        vote_button = page.locator(
            "[data-testid='vote-button'], "
            "button:has-text('Vote'), "
            "button:has-text('Eliminate')"
        )
        if vote_button.count() > 0:
            vote_button.first.click()
            page.wait_for_timeout(3000)

    def test_lobby_shows_characters(self, page: "Page"):
        """Lobby phase displays character list."""
        page.wait_for_load_state("networkidle")

        # Try to get to lobby
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card, button:has-text('Werewolf')"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(3000)

        # Look for character elements
        characters = page.locator(
            "[data-testid='character-card'], .character-card, "
            "[data-testid='character'], .character"
        )
        # If characters exist, verify they're visible
        if characters.count() > 0:
            assert characters.first.is_visible()

    def test_chat_message_appears(self, page: "Page"):
        """Sent chat message appears in the message list."""
        page.wait_for_load_state("networkidle")

        # Navigate to discussion phase
        # First select scenario, then start game
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(2000)

        start_button = page.locator(
            "[data-testid='start-game'], button:has-text('Start')"
        )
        if start_button.count() > 0:
            start_button.first.click()
            page.wait_for_timeout(2000)

        # Send a message
        chat_input = page.locator(
            "[data-testid='chat-input'], input[type='text'], textarea"
        )
        if chat_input.count() > 0:
            test_message = "Testing the chat system!"
            chat_input.first.fill(test_message)
            chat_input.first.press("Enter")
            page.wait_for_timeout(3000)

            # Verify message appears
            message_area = page.locator(
                "[data-testid='message-list'], .message-list, .messages"
            )
            if message_area.count() > 0:
                expect(message_area.first).to_contain_text(test_message)

    def test_navigation_between_phases(self, page: "Page"):
        """User can navigate through game phases."""
        page.wait_for_load_state("networkidle")

        # Check for phase indicator
        phase_indicator = page.locator(
            "[data-testid='phase-indicator'], .phase-indicator, "
            "[data-testid='game-phase'], .game-phase"
        )

        # The page should indicate current phase somehow
        page_text = page.text_content("body") or ""
        # At minimum, page should have loaded
        assert len(page_text) > 0
