# Playwright MCP

This directory stores the generated MCP configuration for this Python framework.

- `scripts/playwright_mcp.py` rebuilds `playwright.config.json` from the repo's Python settings.
- The generated config reuses `.auth/storageState.json` when it exists.
- Start the server with `python3 scripts/playwright_mcp.py`.
