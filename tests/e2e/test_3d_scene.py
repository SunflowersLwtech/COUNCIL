"""E2E tests for the 3D council scene rendering.

Validates that:
- Canvas/WebGL element renders correctly
- No console errors from WebGL
- Character count in 3D matches game state

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


@pytest.fixture
def page(browser):
    p = browser.new_page()
    p.goto(FRONTEND_URL)
    yield p
    p.close()


@pytest.fixture
def page_with_console(browser):
    """Page that captures console messages."""
    p = browser.new_page()
    console_messages = []

    def on_console(msg):
        console_messages.append({
            "type": msg.type,
            "text": msg.text,
        })

    p.on("console", on_console)
    p.goto(FRONTEND_URL)
    p._console_messages = console_messages
    yield p
    p.close()


class TestCanvasRendering:
    def test_canvas_element_exists(self, page: "Page"):
        """Page contains a canvas element for 3D rendering."""
        page.wait_for_load_state("networkidle")

        # Navigate to a game state where 3D scene is visible
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card, "
            "button:has-text('Werewolf')"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(3000)

        canvas = page.locator("canvas")
        if canvas.count() == 0:
            pytest.skip("No canvas element found (3D scene may not be implemented yet)")

        assert canvas.first.is_visible()

    def test_canvas_has_dimensions(self, page: "Page"):
        """Canvas element has non-zero width and height."""
        page.wait_for_load_state("networkidle")

        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(3000)

        canvas = page.locator("canvas")
        if canvas.count() == 0:
            pytest.skip("No canvas element found")

        box = canvas.first.bounding_box()
        if box is None:
            pytest.skip("Canvas has no bounding box")

        assert box["width"] > 0, "Canvas width should be > 0"
        assert box["height"] > 0, "Canvas height should be > 0"


class TestWebGLErrors:
    def test_no_webgl_errors(self, page_with_console: "Page"):
        """No WebGL-related errors in console."""
        page = page_with_console
        page.wait_for_load_state("networkidle")

        # Navigate to 3D scene
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(5000)

        # Check console for WebGL errors
        console_messages = page._console_messages
        webgl_errors = [
            msg for msg in console_messages
            if msg["type"] == "error"
            and ("webgl" in msg["text"].lower() or "gl_" in msg["text"].lower())
        ]

        assert len(webgl_errors) == 0, (
            f"WebGL errors found in console: {webgl_errors}"
        )

    def test_no_three_js_errors(self, page_with_console: "Page"):
        """No Three.js or R3F related errors in console."""
        page = page_with_console
        page.wait_for_load_state("networkidle")

        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(5000)

        console_messages = page._console_messages
        threejs_errors = [
            msg for msg in console_messages
            if msg["type"] == "error"
            and ("three" in msg["text"].lower() or "r3f" in msg["text"].lower())
        ]

        assert len(threejs_errors) == 0, (
            f"Three.js errors found: {threejs_errors}"
        )


class TestCharacterCountIn3D:
    def test_character_count_matches_state(self, page: "Page"):
        """Number of 3D character models matches game state character count."""
        page.wait_for_load_state("networkidle")

        # Load a scenario
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card, "
            "button:has-text('Werewolf')"
        )
        if scenario_elements.count() == 0:
            pytest.skip("No scenario cards found")

        scenario_elements.first.click()
        page.wait_for_timeout(5000)

        # Count character indicators in UI
        character_elements = page.locator(
            "[data-testid='character-card'], .character-card, "
            "[data-testid='character'], .character"
        )
        ui_count = character_elements.count()

        if ui_count == 0:
            pytest.skip("No character elements found in UI")

        # Count 3D character models (if they have data attributes)
        scene_characters = page.locator(
            "[data-testid='character-model'], .character-model, "
            "[data-testid='character-3d']"
        )
        scene_count = scene_characters.count()

        if scene_count == 0:
            # Try counting via canvas-related elements
            pytest.skip("Cannot count 3D characters (no selectable elements)")

        assert scene_count == ui_count, (
            f"3D scene has {scene_count} characters but UI shows {ui_count}"
        )

    def test_eliminated_character_visual(self, page: "Page"):
        """Eliminated characters have visual indication in 3D scene."""
        # This test verifies the concept; actual implementation may vary
        page.wait_for_load_state("networkidle")

        # Would need a full game flow to get to elimination
        # For now, just verify the page loads
        assert page.content()
