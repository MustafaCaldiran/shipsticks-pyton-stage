"""Launch the Playwright MCP server using this repo's Python settings."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings
from fixtures.global_setup import STORAGE_STATE_PATH, run_global_setup

MCP_CONFIG_PATH = REPO_ROOT / ".mcp" / "playwright.config.json"
PASSTHROUGH_FLAGS = {"-h", "--help", "-V", "--version"}


def _browser_name() -> str:
    for browser in settings.browsers:
        if browser in {"chromium", "firefox", "webkit"}:
            return browser
    return "chromium"


def _build_config() -> dict:
    context_options = {
        "baseURL": settings.base_url,
        "ignoreHTTPSErrors": True,
        "viewport": settings.VIEWPORT,
    }
    if STORAGE_STATE_PATH.exists():
        context_options["storageState"] = str(STORAGE_STATE_PATH)

    return {
        "browser": {
            "browserName": _browser_name(),
            "isolated": True,
            "launchOptions": {
                "headless": not settings.headed,
                "slowMo": settings.slow_mo,
                "args": [
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                ],
            },
            "contextOptions": context_options,
        }
    }


def main() -> int:
    if shutil.which("npx") is None:
        raise SystemExit("npx was not found. Install Node.js 18+ before starting Playwright MCP.")

    passthrough_only = any(arg in PASSTHROUGH_FLAGS for arg in sys.argv[1:])
    cmd = ["npx", "@playwright/mcp@latest"]
    if passthrough_only:
        cmd.extend(sys.argv[1:])
    else:
        MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        run_global_setup()
        MCP_CONFIG_PATH.write_text(json.dumps(_build_config(), indent=2) + "\n", encoding="utf-8")
        cmd.extend(["--config", str(MCP_CONFIG_PATH), *sys.argv[1:]])
        print(f"Launching Playwright MCP with {MCP_CONFIG_PATH}")

    completed = subprocess.run(cmd, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
