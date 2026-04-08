"""
BasePage — shared foundation for every page object.

Encapsulates the anti-flake patterns that the JS framework uses:
  - typeWithFocusGuard  → type_with_focus_guard()
  - chat widget removal → dismiss_chat_widget()
  - autocomplete waits  → wait_for_autocomplete()
  - cookie banner       → accept_cookies_if_present()

Python-specific fixes applied here:
  - pressSequentially uses keyword arg `delay` (not options object)
  - MutationObserver injection is done via add_init_script for reliability
  - route() patterns use glob syntax (not JS RegExp)
  - try/except replaces JS try/catch; timeout errors are caught explicitly
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect, TimeoutError as PlaywrightTimeout

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

log = logging.getLogger("pages")

# Domains blocked at the network level to prevent chat widgets from loading
CHAT_WIDGET_PATTERNS = [
    re.compile(r"intercom|chat-widget|livechat|zendesk|freshchat|crisp|tawk", re.I),
]

# JS snippet injected via add_init_script to remove Intercom elements
# as soon as they appear in the DOM (before they can steal focus).
_CHAT_WIDGET_INIT_SCRIPT = """
() => {
    const selectors = [
        '#launcher',
        'iframe[id*="launcher"]',
        'iframe[name*="intercom"]',
        'iframe[title*="intercom"]',
        '#intercom-container',
        '[class*="intercom-"]'
    ];
    const remove = () => selectors.forEach(s =>
        document.querySelectorAll(s).forEach(el => el.remove())
    );
    const obs = new MutationObserver(remove);
    obs.observe(document.documentElement, { childList: true, subtree: true });
    window.__chatObserver = obs;
}
"""


class BasePage:
    """Every page object inherits from this class."""

    def __init__(self, page: "Page", base_url: str = ""):
        self.page = page
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, path: str = "/") -> None:
        """Navigate to *path* relative to base_url, wait for DOM ready."""
        url = f"{self.base_url}{path}" if not path.startswith("http") else path
        self.page.goto(url, wait_until="domcontentloaded")

    # ------------------------------------------------------------------
    # Input helpers — Python-native reimplementations of JS helpers
    # ------------------------------------------------------------------

    def type_carefully(
        self,
        locator: "Locator",
        text: str,
        *,
        delay: int = 50,
        clear_first: bool = True,
    ) -> None:
        """
        Type character-by-character with a delay.

        This triggers autocomplete dropdowns that only respond to keyboard
        events (fill() sets the value programmatically and skips them).
        """
        if clear_first:
            locator.click()
            locator.fill("")
        locator.press_sequentially(text, delay=delay)

    def type_with_focus_guard(self, locator: "Locator", text: str, retries: int = 3) -> None:
        """
        Type text into a field, retrying if focus is stolen.

        Chat widgets (Intercom) frequently grab focus mid-typing.
        This method detects the theft by checking the input value after
        typing and retries up to *retries* times, dismissing the chat
        widget between attempts.

        Fixes over old Python version:
          - Uses expect().to_have_value() as final fallback instead of assert
          - Dismisses chat widget between retries (the actual fix)
          - Increased default retries from 3 to 3 (same) but with logging
        """
        for attempt in range(retries):
            locator.click()
            locator.fill("")
            locator.press_sequentially(text, delay=50)
            actual = locator.input_value()
            if actual == text:
                return  # Success
            log.warning(
                "Focus guard retry %d/%d — expected %r, got %r",
                attempt + 1, retries, text, actual,
            )
            self.dismiss_chat_widget()

        # Final assertion — will produce a clear Playwright error message
        expect(locator).to_have_value(text, timeout=5000)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_element(self, locator: "Locator", timeout: int = 10000) -> None:
        """Wait until *locator* is visible."""
        expect(locator).to_be_visible(timeout=timeout)

    def wait_for_autocomplete(self, timeout: int = 15000) -> "Locator":
        """
        Wait for an autocomplete dropdown to appear.

        Looks for any of the common autocomplete containers:
          - [role="listbox"]        (ARIA)
          - .pac-container          (Google Places)
          - [data-testid*="auto"]   (custom)
        """
        listbox = self.page.locator(
            '[role="listbox"], .pac-container, [data-testid*="autocomplete"]'
        )
        expect(listbox.first).to_be_visible(timeout=timeout)
        return listbox

    def wait_for_autocomplete_option(
        self,
        text_or_regex: str | re.Pattern,
        timeout: int = 15000,
    ) -> "Locator":
        """Wait for a specific option inside the autocomplete dropdown."""
        if isinstance(text_or_regex, str):
            option = self.page.get_by_role("option", name=text_or_regex)
        else:
            option = self.page.get_by_role("option", name=text_or_regex)
        expect(option.first).to_be_visible(timeout=timeout)
        return option

    # ------------------------------------------------------------------
    # Modal / widget dismissal
    # ------------------------------------------------------------------

    def dismiss_country_note_if_present(self, timeout: int = 8000) -> None:
        """Dismiss the 'I understand' country-note modal if it appears."""
        try:
            btn = self.page.get_by_role("button", name="I understand")
            btn.wait_for(state="visible", timeout=timeout)
            btn.click()
            btn.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeout:
            pass  # Modal wasn't present — expected in many flows

    def accept_cookies_if_present(self, timeout: int = 5000) -> None:
        """Click the cookie-consent banner if it appears."""
        try:
            btn = self.page.get_by_role("button", name=re.compile(r"(?i)accept.*cookies|accept all"))
            btn.wait_for(state="visible", timeout=timeout)
            btn.click()
            btn.wait_for(state="hidden", timeout=3000)
        except PlaywrightTimeout:
            pass

    def dismiss_chat_widget(self) -> None:
        """
        Remove Intercom chat widget elements from the DOM.

        Uses evaluate() to run synchronous DOM cleanup.  Also installs a
        MutationObserver so the widget is auto-removed if it reappears.
        """
        self.page.evaluate("""
            () => {
                const selectors = [
                    '#launcher',
                    'iframe[id*="launcher"]',
                    'iframe[name*="intercom"]',
                    'iframe[title*="intercom"]',
                    '#intercom-container',
                    '[class*="intercom-"]'
                ];
                selectors.forEach(s =>
                    document.querySelectorAll(s).forEach(el => el.remove())
                );
                if (!window.__chatObserver) {
                    const obs = new MutationObserver(() =>
                        selectors.forEach(s =>
                            document.querySelectorAll(s).forEach(el => el.remove())
                        )
                    );
                    obs.observe(document.documentElement, {
                        childList: true, subtree: true
                    });
                    window.__chatObserver = obs;
                }
            }
        """)

    def dismiss_chat_widget_if_present(self) -> None:
        """Alias kept for parity with the JavaScript page objects."""
        self.dismiss_chat_widget()

    # ------------------------------------------------------------------
    # Page setup (call in goto() of subclasses)
    # ------------------------------------------------------------------

    def block_chat_widgets(self) -> None:
        """
        Two-layer chat widget blocking:
          1. Network-level: abort requests to chat domains
          2. DOM-level: init script removes elements on mutation
        """
        for pattern in CHAT_WIDGET_PATTERNS:
            self.page.route(pattern, lambda route: route.abort())
        self.page.add_init_script(_CHAT_WIDGET_INIT_SCRIPT)

    # ------------------------------------------------------------------
    # Regex helper (used in page objects for dynamic locators)
    # ------------------------------------------------------------------

    @staticmethod
    def escape_regex(value: str) -> str:
        """Escape special regex characters in *value*."""
        return re.escape(value)
