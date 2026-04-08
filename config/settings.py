"""Central runtime settings shared by the Python framework."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://app.staging.shipsticks.com"
ENV_BASE_URLS = {
    "staging": DEFAULT_BASE_URL,
    "stage": DEFAULT_BASE_URL,
    "prod": "https://www.shipsticks.com",
    "production": "https://www.shipsticks.com",
}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_base_url() -> str:
    env_name = (os.getenv("TEST_ENV") or "").strip().lower()
    explicit_base_url = os.getenv("BASE_URL")
    if explicit_base_url:
        return explicit_base_url.rstrip("/")
    if env_name and env_name in ENV_BASE_URLS:
        return ENV_BASE_URLS[env_name].rstrip("/")
    return DEFAULT_BASE_URL


def _derive_web_base_url(base_url: str) -> str:
    if "://app." in base_url:
        return base_url.replace("://app.", "://www.app.", 1)
    return base_url


class Settings:
    """Immutable-style config object loaded once at import time."""

    VIEWPORT = {"width": 1280, "height": 800}
    EXPECT_TIMEOUT = 15_000
    TYPING_DELAY = 50

    def __init__(self) -> None:
        self.test_env: str = (os.getenv("TEST_ENV") or "staging").strip().lower()
        self.base_url: str = _resolve_base_url()
        self.web_base_url: str = _derive_web_base_url(self.base_url)

        self.headed: bool = _as_bool(os.getenv("HEADED"))
        self.slow_mo: int = int(os.getenv("SLOW_MO", "0"))
        self.timeout: int = int(os.getenv("TIMEOUT", "60000"))
        self.verbose: bool = _as_bool(os.getenv("VERBOSE"))

        self.browsers: list[str] = [
            browser.strip()
            for browser in os.getenv("BROWSERS", "chromium").split(",")
            if browser.strip()
        ]

        self.workers: int = int(os.getenv("WORKERS", "1"))
        self.fully_parallel: bool = _as_bool(os.getenv("FULLY_PARALLEL"))
        self.scenarios: list[str] = [
            scenario.strip()
            for scenario in os.getenv("SCENARIOS", "").split(",")
            if scenario.strip()
        ]

        self.auth_email: str = os.getenv("AUTH_EMAIL", "john@gmail.com")
        self.auth_password: str = os.getenv("AUTH_PASSWORD", "Password")
        self.prod_email: str = os.getenv("PROD_EMAIL", self.auth_email)
        self.prod_password: str = os.getenv("PROD_PASSWORD", self.auth_password)


settings = Settings()
