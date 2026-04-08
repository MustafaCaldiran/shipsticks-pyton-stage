"""Pytest fixture hub aligned with the JavaScript Playwright framework."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import BrowserContext, Page

from config.settings import settings
from fixtures.global_setup import STORAGE_STATE_PATH, run_global_setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@pytest.fixture(scope="session", autouse=True)
def _global_auth_setup():
    run_global_setup()
    yield


@pytest.fixture(scope="session")
def browser_type_launch_args():
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
    return {
        "viewport": settings.VIEWPORT,
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def base_url():
    return settings.base_url


@pytest.fixture(autouse=True)
def _configure_page_defaults(page: Page):
    page.set_default_timeout(settings.timeout)
    page.set_default_navigation_timeout(settings.timeout)
    yield


@pytest.fixture()
def api_context(playwright):
    context = playwright.request.new_context(
        base_url=settings.base_url,
        ignore_https_errors=True,
    )
    yield context
    context.dispose()


@pytest.fixture()
def authenticated_api_context(playwright):
    kwargs = {
        "base_url": settings.base_url,
        "ignore_https_errors": True,
    }
    if STORAGE_STATE_PATH.exists():
        kwargs["storage_state"] = str(STORAGE_STATE_PATH)
    context = playwright.request.new_context(**kwargs)
    yield context
    context.dispose()


@pytest.fixture()
def auth_context(browser) -> BrowserContext:
    kwargs = {
        "viewport": settings.VIEWPORT,
        "ignore_https_errors": True,
    }
    if STORAGE_STATE_PATH.exists():
        kwargs["storage_state"] = str(STORAGE_STATE_PATH)
    context = browser.new_context(**kwargs)
    yield context
    context.close()


@pytest.fixture()
def auth_page(auth_context) -> Page:
    page = auth_context.new_page()
    yield page
    page.close()
