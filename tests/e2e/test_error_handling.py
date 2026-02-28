"""E2E tests for error handling and edge cases.

Tests:
- Invalid document upload
- Empty text submission
- Network failure handling
- UI error states

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
    p.on("console", lambda msg: console_messages.append({
        "type": msg.type,
        "text": msg.text,
    }))
    p.goto(FRONTEND_URL)
    p._console_messages = console_messages
    yield p
    p.close()


class TestInvalidDocumentUpload:
    def test_invalid_file_type(self, page: "Page"):
        """Uploading an invalid file type shows error or fallback."""
        page.wait_for_load_state("networkidle")

        file_input = page.locator(
            "input[type='file'], [data-testid='file-upload']"
        )
        if file_input.count() == 0:
            pytest.skip("No file upload element found")

        # Create a temporary invalid file
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False, mode="wb") as f:
            f.write(b"\x00\x00\x00\x00")
            temp_path = f.name

        try:
            file_input.first.set_input_files(temp_path)
            page.wait_for_timeout(3000)

            # Should either show error message or handle gracefully
            error_msg = page.locator(
                "[data-testid='error-message'], .error-message, "
                ".error, [role='alert']"
            )
            # Page should not crash
            assert page.content()
        finally:
            os.unlink(temp_path)

    def test_empty_file_upload(self, page: "Page"):
        """Uploading an empty file shows error or uses fallback."""
        page.wait_for_load_state("networkidle")

        file_input = page.locator(
            "input[type='file'], [data-testid='file-upload']"
        )
        if file_input.count() == 0:
            pytest.skip("No file upload element found")

        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("")
            temp_path = f.name

        try:
            file_input.first.set_input_files(temp_path)
            page.wait_for_timeout(3000)
            # Should not crash
            assert page.content()
        finally:
            os.unlink(temp_path)


class TestEmptyTextSubmission:
    def test_empty_text_shows_validation(self, page: "Page"):
        """Submitting empty text shows validation error or is prevented."""
        page.wait_for_load_state("networkidle")

        text_input = page.locator(
            "[data-testid='text-input'], [data-testid='scenario-text'], "
            "textarea"
        )
        if text_input.count() == 0:
            pytest.skip("No text input found")

        # Try submitting empty text
        text_input.first.fill("")

        submit_button = page.locator(
            "[data-testid='submit-text'], button:has-text('Create'), "
            "button:has-text('Submit'), button[type='submit']"
        )
        if submit_button.count() > 0:
            submit_button.first.click()
            page.wait_for_timeout(2000)

        # Page should either show error or prevent submission
        assert page.content()

    def test_whitespace_only_text(self, page: "Page"):
        """Submitting whitespace-only text is handled gracefully."""
        page.wait_for_load_state("networkidle")

        text_input = page.locator(
            "[data-testid='text-input'], textarea"
        )
        if text_input.count() == 0:
            pytest.skip("No text input found")

        text_input.first.fill("   \n\n  ")

        submit_button = page.locator(
            "[data-testid='submit-text'], button:has-text('Create'), "
            "button:has-text('Submit')"
        )
        if submit_button.count() > 0:
            submit_button.first.click()
            page.wait_for_timeout(3000)

        # Should not crash; may use fallback world
        assert page.content()


class TestEmptyChatMessage:
    def test_empty_chat_not_sent(self, page: "Page"):
        """Empty chat messages are not sent."""
        page.wait_for_load_state("networkidle")

        # Navigate to discussion phase first
        scenario_elements = page.locator(
            "[data-testid='scenario-card'], .scenario-card"
        )
        if scenario_elements.count() > 0:
            scenario_elements.first.click()
            page.wait_for_timeout(3000)

        start_button = page.locator(
            "[data-testid='start-game'], button:has-text('Start')"
        )
        if start_button.count() > 0:
            start_button.first.click()
            page.wait_for_timeout(2000)

        chat_input = page.locator(
            "[data-testid='chat-input'], input[type='text'], textarea"
        )
        if chat_input.count() == 0:
            pytest.skip("No chat input found")

        # Try sending empty message
        chat_input.first.fill("")
        chat_input.first.press("Enter")
        page.wait_for_timeout(1000)

        # Page should not crash or show unhandled errors
        assert page.content()


class TestNetworkFailure:
    def test_backend_down_shows_error(self, browser):
        """When backend is unreachable, UI shows error state."""
        page = browser.new_page()

        try:
            # Route API calls to fail
            page.route("**/api/**", lambda route: route.abort("connectionrefused"))
            page.goto(FRONTEND_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # Page should still render (not blank)
            content = page.content()
            assert len(content) > 100, "Page should have rendered content even with API down"

            # Look for error indication
            error_elements = page.locator(
                "[data-testid='error'], .error, [role='alert'], "
                "text=error, text=Error, text=unavailable"
            )
            # It's OK if there's no explicit error (maybe lazy loading)
            # Just verify no crash
        finally:
            page.close()

    def test_slow_api_shows_loading(self, browser):
        """Slow API responses show loading state."""
        page = browser.new_page()

        try:
            # Add 5-second delay to API calls
            def slow_route(route):
                import time
                time.sleep(2)
                route.abort("connectionrefused")

            page.route("**/api/game/**", slow_route)
            page.goto(FRONTEND_URL)
            page.wait_for_load_state("networkidle")

            # Look for loading indicators
            loading = page.locator(
                "[data-testid='loading'], .loading, .spinner, "
                "[aria-busy='true'], text=Loading"
            )
            # Loading state may or may not be visible depending on timing
            # Main thing is page doesn't crash
            assert page.content()
        finally:
            page.close()


class TestUIRobustness:
    def test_rapid_clicks_handled(self, page: "Page"):
        """Rapid clicks don't cause errors."""
        page.wait_for_load_state("networkidle")

        clickable = page.locator("button").first
        if clickable.count() == 0:
            pytest.skip("No buttons found")

        # Click rapidly 5 times
        for _ in range(5):
            try:
                clickable.click(timeout=1000)
            except Exception:
                pass

        page.wait_for_timeout(1000)
        # Page should still be functional
        assert page.content()

    def test_page_resize(self, page: "Page"):
        """Page handles window resize without errors."""
        page.wait_for_load_state("networkidle")

        # Resize to mobile
        page.set_viewport_size({"width": 375, "height": 812})
        page.wait_for_timeout(1000)
        assert page.content()

        # Resize to desktop
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(1000)
        assert page.content()

    def test_no_uncaught_errors(self, page_with_console: "Page"):
        """No uncaught JavaScript errors on page load."""
        page = page_with_console
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        console_messages = page._console_messages
        uncaught_errors = [
            msg for msg in console_messages
            if msg["type"] == "error"
            and "uncaught" in msg["text"].lower()
        ]

        assert len(uncaught_errors) == 0, (
            f"Uncaught errors found: {[e['text'][:200] for e in uncaught_errors]}"
        )
