"""Global auth setup matching the JavaScript framework."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from config.settings import settings

log = logging.getLogger("global_setup")

AUTH_CREDENTIALS = {
    "email": settings.auth_email,
    "password": settings.auth_password,
}
STORAGE_STATE_PATH = Path(__file__).resolve().parent.parent / ".auth" / "storageState.json"
CSRF_PATTERN = re.compile(r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"')


def run_global_setup() -> Path:
    """Log in once via Devise and persist the session storage state."""
    base_url = settings.api_url

    log.info("globalSetup: logging in against %s (TEST_ENV=%s)", base_url, settings.test_env)
    STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        api_context = playwright.request.new_context(
            base_url=base_url,
            ignore_https_errors=True,
        )

        csrf_token = ""
        for attempt in range(1, 4):
            response = api_context.get("/users/sign_in")
            html = response.text()
            match = CSRF_PATTERN.search(html)
            if match:
                csrf_token = match.group(1)
                break
            if attempt == 3:
                log.warning(
                    "globalSetup: %s server did not return CSRF token after 3 attempts. "
                    "Skipping login. Tests requiring auth may fail.",
                    settings.test_env,
                )
                api_context.dispose()
                return STORAGE_STATE_PATH
            time.sleep(2)

        body = urlencode(
            {
                "utf8": "✓",
                "authenticity_token": csrf_token,
                "user[email]": AUTH_CREDENTIALS["email"],
                "user[password]": AUTH_CREDENTIALS["password"],
                "user[remember_me]": "0",
            }
        )
        login_response = api_context.post(
            "/users/sign_in",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": f"{base_url}/users/sign_in",
            },
            data=body,
        )
        if not login_response.ok:
            log.warning(
                "globalSetup: login request failed with status %s. Skipping session save.",
                login_response.status,
            )
            api_context.dispose()
            return STORAGE_STATE_PATH

        api_context.storage_state(path=str(STORAGE_STATE_PATH))
        api_context.dispose()
        log.info("globalSetup: API login complete, session saved to %s", STORAGE_STATE_PATH)
        return STORAGE_STATE_PATH
