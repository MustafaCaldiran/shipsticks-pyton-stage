"""Global auth setup aligned with the JavaScript repo's API login flow."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from config.settings import settings

log = logging.getLogger("global_setup")

STORAGE_STATE_PATH = Path(__file__).resolve().parent.parent / ".auth" / "storageState.json"
CSRF_PATTERN = re.compile(r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"')


def _extract_csrf_token(html: str) -> str:
    match = CSRF_PATTERN.search(html)
    return match.group(1) if match else ""


def run_global_setup() -> Path:
    """Create a persisted authenticated session if the environment allows it."""
    STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        api_context = playwright.request.new_context(
            base_url=settings.web_base_url,
            ignore_https_errors=True,
        )

        csrf_token = ""
        for attempt in range(1, 4):
            login_page = api_context.get("/users/sign_in")
            csrf_token = _extract_csrf_token(login_page.text())
            if csrf_token:
                break
            if attempt == 3:
                log.warning(
                    "global_setup: %s did not return a CSRF token after 3 attempts. "
                    "Authenticated tests may fail.",
                    settings.web_base_url,
                )
                api_context.dispose()
                return STORAGE_STATE_PATH
            time.sleep(2)

        response = api_context.post(
            "/users/sign_in",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": f"{settings.web_base_url}/users/sign_in",
            },
            data=(
                "utf8=%E2%9C%93"
                f"&authenticity_token={csrf_token}"
                f"&user%5Bemail%5D={settings.auth_email}"
                f"&user%5Bpassword%5D={settings.auth_password}"
                "&user%5Bremember_me%5D=0"
            ),
        )

        if not response.ok:
            log.warning(
                "global_setup: login request failed with status %s. "
                "Authenticated tests may fail.",
                response.status,
            )
            api_context.dispose()
            return STORAGE_STATE_PATH

        api_context.storage_state(path=str(STORAGE_STATE_PATH))
        api_context.dispose()
        log.info("global_setup: session saved to %s", STORAGE_STATE_PATH)
        return STORAGE_STATE_PATH
