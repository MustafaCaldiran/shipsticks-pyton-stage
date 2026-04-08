"""Runtime settings aligned with the JavaScript Playwright repo."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

ENV_CONFIGS = {
    "local": {
        "app_url": "http://localhost:3000",
        "api_url": "http://localhost:3000",
    },
    "staging": {
        "app_url": "https://www.app.staging.shipsticks.com",
        "api_url": "https://www.staging.shipsticks.com",
    },
    "production": {
        "app_url": "https://www.shipsticks.com",
        "api_url": "https://www.shipsticks.com",
    },
}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    VIEWPORT = {"width": 1280, "height": 800}
    EXPECT_TIMEOUT = 15_000

    def __init__(self) -> None:
        self.test_env = (os.getenv("TEST_ENV") or "staging").strip().lower()
        env_config = ENV_CONFIGS.get(self.test_env)
        if env_config is None:
            valid = ", ".join(ENV_CONFIGS)
            raise ValueError(f'Unknown TEST_ENV: "{self.test_env}". Valid options: {valid}')

        base_url_override = os.getenv("BASE_URL")
        self.base_url = (base_url_override or env_config["app_url"]).rstrip("/")
        self.api_url = (base_url_override or env_config["api_url"]).rstrip("/")

        self.headed = _as_bool(os.getenv("HEADED"))
        self.slow_mo = int(os.getenv("SLOW_MO", "0"))
        self.timeout = int(os.getenv("TIMEOUT", "60000"))
        self.verbose = _as_bool(os.getenv("VERBOSE"))
        self.fully_parallel = _as_bool(os.getenv("FULLY_PARALLEL"))
        self.workers = int(os.getenv("WORKERS", "1" if os.getenv("CI") else "0"))
        self.browsers = [
            browser.strip()
            for browser in os.getenv("BROWSERS", "chromium").split(",")
            if browser.strip()
        ]
        self.scenarios = [
            scenario.strip()
            for scenario in os.getenv("SCENARIOS", "").split(",")
            if scenario.strip()
        ]

        self.auth_email = os.getenv("AUTH_EMAIL", "john@gmail.com")
        self.auth_password = os.getenv("AUTH_PASSWORD", "Password")
        self.prod_email = os.getenv("PROD_EMAIL", "shipsticksprodtest@gmail.com")
        self.prod_password = os.getenv("PROD_PASSWORD", "Password")


settings = Settings()
