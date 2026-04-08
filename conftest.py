"""
Root conftest — the fixture hub for the entire test suite.

Design decisions:
  - Session-scoped browser launch args (one browser per run for speed)
  - Function-scoped contexts by default (isolation between tests)
  - Global auth setup runs once; authenticated tests load the storage state
  - All config flows through config.settings — no env var reads here
  - Page-object fixtures are intentionally NOT provided; tests instantiate
    them explicitly so readers can see the full dependency chain.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, Page

from config.settings import settings
from fixtures.global_setup import STORAGE_STATE_PATH, run_global_setup

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


# ---------------------------------------------------------------------------
# Session-scoped: run global auth setup once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _global_auth_setup():
    """Authenticate once and save storage state for the test run."""
    run_global_setup()
    yield
    # Cleanup could go here if needed


# ---------------------------------------------------------------------------
# Playwright launch / context overrides
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Override Playwright browser launch options."""
    return {
        "headless": not settings.headed,
        "slow_mo": settings.slow_mo,
        "args": [
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
        ],
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """Override Playwright browser context defaults."""
    return {
        "viewport": settings.VIEWPORT,
        "ignore_https_errors": True,
    }


# ---------------------------------------------------------------------------
# Base URL fixture (used by pytest-playwright)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url():
    return settings.base_url


# ---------------------------------------------------------------------------
# Runtime defaults
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _configure_page_defaults(page: Page):
    """Apply the framework's timeouts to every test page."""
    page.set_default_timeout(settings.timeout)
    page.set_default_navigation_timeout(settings.timeout)
    yield


# ---------------------------------------------------------------------------
# API contexts
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_context(playwright):
    """Fresh API request context targeting the web host used by auth endpoints."""
    context = playwright.request.new_context(
        base_url=settings.web_base_url,
        ignore_https_errors=True,
    )
    yield context
    context.dispose()


@pytest.fixture()
def authenticated_api_context(playwright):
    """API context preloaded with the saved authenticated storage state."""
    storage_state = str(STORAGE_STATE_PATH) if STORAGE_STATE_PATH.exists() else None
    context = playwright.request.new_context(
        base_url=settings.web_base_url,
        ignore_https_errors=True,
        storage_state=storage_state,
    )
    yield context
    context.dispose()


# ---------------------------------------------------------------------------
# Authenticated context (loads saved storage state)
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_context(browser, base_url) -> BrowserContext:
    """
    A browser context pre-loaded with the session from global setup.

    Use this fixture in tests that need an already-logged-in user.
    """
    context_kwargs = {
        "viewport": settings.VIEWPORT,
        "ignore_https_errors": True,
    }
    if STORAGE_STATE_PATH.exists():
        context_kwargs["storage_state"] = str(STORAGE_STATE_PATH)
    context = browser.new_context(**context_kwargs)
    yield context
    context.close()


@pytest.fixture()
def auth_page(auth_context) -> Page:
    """A page inside the authenticated context."""
    page = auth_context.new_page()
    yield page
    page.close()
