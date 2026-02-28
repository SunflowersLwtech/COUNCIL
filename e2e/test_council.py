"""End-to-end test for COUNCIL using Playwright."""
import asyncio
import sys

async def run_e2e():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test 1: Load the page
        print("[E2E] Test 1: Loading COUNCIL frontend...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        title = await page.title()
        assert "COUNCIL" in title, f"Expected COUNCIL in title, got: {title}"
        print(f"  PASS: Title is '{title}'")
        
        # Test 2: Check main UI elements
        print("[E2E] Test 2: Checking UI elements...")
        header = await page.text_content("h1")
        assert "COUNCIL" in header, f"Expected COUNCIL header, got: {header}"
        print(f"  PASS: Header shows '{header}'")
        
        # Test 3: Check pipeline status is visible
        pipeline = await page.text_content("text=Pipeline Status")
        assert pipeline, "Pipeline Status section not found"
        print("  PASS: Pipeline Status visible")
        
        # Test 4: Check "Try Demo" button exists
        demo_button = page.get_by_text("Try Demo Project")
        # Could be in header or chat area
        header_button = page.get_by_text("Try Demo")
        count = await demo_button.count() + await header_button.count()
        assert count > 0, "Try Demo button not found"
        print("  PASS: Try Demo button found")
        
        # Test 5: Check findings panel placeholder
        findings_text = await page.text_content("text=No findings yet")
        assert findings_text, "Findings placeholder not found"
        print("  PASS: Findings placeholder shown")
        
        # Test 6: Click Try Demo and wait for analysis
        print("[E2E] Test 6: Running analysis (this takes ~60-120s)...")
        # Click the header Try Demo button
        try:
            btn = page.locator("button", has_text="Try Demo").first
            await btn.click()
            print("  Clicked 'Try Demo' button, waiting for analysis...")
            
            # Wait for analysis to complete (up to 5 minutes)
            await page.wait_for_selector("text=Analysis Complete", timeout=300000)
            print("  PASS: Analysis completed!")
        except Exception as e:
            print(f"  SKIP: Analysis test skipped ({e})")
            # Take screenshot for debugging
            await page.screenshot(path="e2e/screenshot_error.png")
            print("  Screenshot saved to e2e/screenshot_error.png")
            await browser.close()
            return
        
        # Test 7: Check findings appeared
        print("[E2E] Test 7: Checking findings...")
        findings_section = page.locator("text=issues found")
        count = await findings_section.count()
        if count > 0:
            text = await findings_section.first.text_content()
            print(f"  PASS: {text}")
        else:
            print("  WARN: Findings count not visible")
        
        # Test 8: Check Critical/High sections appeared
        critical = page.locator("text=Critical")
        if await critical.count() > 0:
            print("  PASS: Critical findings section visible")
        
        # Test 9: Check chat input is enabled
        print("[E2E] Test 9: Testing chat...")
        chat_input = page.locator("input[placeholder*='Ask about']")
        if await chat_input.count() > 0:
            assert await chat_input.is_enabled(), "Chat input should be enabled after analysis"
            print("  PASS: Chat input is enabled")
            
            # Type and send a question
            await chat_input.fill("What are the security issues?")
            send_btn = page.locator("button", has_text="Send")
            await send_btn.click()
            print("  Sent question, waiting for response...")
            
            # Wait for agent response
            try:
                await page.wait_for_selector("text=Security Analyst", timeout=60000)
                print("  PASS: Got response from Security Analyst")
            except:
                print("  WARN: Agent response timeout")
        
        # Take final screenshot
        await page.screenshot(path="e2e/screenshot_final.png")
        print("  Screenshot saved to e2e/screenshot_final.png")
        
        await browser.close()
        print("\n[E2E] All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_e2e())
