# Ship Sticks — Python Playwright Automation Framework

A production-ready, interview-quality E2E test automation framework built with **Playwright + Pytest**, re-architected from a JavaScript Playwright framework and a partial Python implementation.

---

## Table of Contents

1. [Framework Architecture](#framework-architecture)
2. [Folder Structure](#folder-structure)
3. [Key Design Decisions](#key-design-decisions)
4. [JS vs Python Implementation Differences](#js-vs-python-implementation-differences)
5. [Known Challenges & Solutions](#known-challenges--solutions)
6. [Network Interception in Python](#network-interception-in-python)
7. [Running Tests](#running-tests)
8. [Environment Switching](#environment-switching)
9. [Reporting](#reporting)
10. [Parallel Execution](#parallel-execution)
11. [Playwright MCP](#playwright-mcp)
12. [Extending the Framework](#extending-the-framework)
13. [Interview Talking Points](#interview-talking-points)

---

## Framework Architecture

```
                        ┌─────────────┐
                        │  pytest.ini │  Configuration
                        └──────┬──────┘
                               │
                        ┌──────▼──────┐
                        │  conftest   │  Fixtures, hooks, browser setup
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
      ┌───────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
      │    Tests     │ │   Pages     │ │   Utils      │
      │              │ │  (POM)      │ │              │
      │ test_booking │ │ BasePage    │ │ network_log  │
      │ test_login   │ │ HomePage    │ │ api_helpers  │
      │ test_e2e     │ │ Booking*    │ │ interception │
      │ test_network │ │ Travelers   │ └──────────────┘
      └──────────────┘ │ Payment     │
                       │ Review      │
                       │ Confirmation│
                       └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │   Config    │  Settings singleton
                       │   Data      │  Test scenarios
                       └─────────────┘
```

**Data flows top-down.** Tests consume page objects; page objects consume utilities. Nothing flows upward. This makes the dependency graph acyclic and each layer independently testable.

---

## Folder Structure

```
shipsticks-python-framework/
│
├── config/
│   ├── __init__.py              # Re-exports `settings`
│   └── settings.py              # Centralized config from env vars
│
├── data/
│   ├── __init__.py
│   └── test_data.py             # Scenarios, auth data, variations
│
├── fixtures/
│   ├── __init__.py
│   └── global_setup.py          # Pre-suite auth + storage state
│
├── pages/
│   ├── __init__.py
│   ├── base_page.py             # Anti-flake helpers, widget blocking
│   ├── home_page.py             # Quote widget, sign-in/up modals
│   ├── booking_step1_page.py    # Items, dates, shipping (most complex)
│   ├── booking_login_page.py    # Order summary verification
│   ├── travelers_page.py        # Traveler details form
│   ├── payment_page.py          # Card entry, coverage, pickup
│   ├── review_page.py           # Final review before payment
│   └── order_confirmation_page.py
│
├── tests/
│   ├── __init__.py
│   ├── test_booking.py          # Scenario-driven Step 1 tests
│   ├── test_login.py            # Sign-up flow
│   ├── test_e2e.py              # Full journey (sign-up → confirmation)
│   ├── test_booking_blocking.py # Bot protection guardrail
│   └── test_network_interception.py  # Spy, mock, failure simulation
│
├── utils/
│   ├── __init__.py
│   ├── network_logger.py        # Traffic capture + cookie dump
│   ├── api_helpers.py           # REST + GraphQL + CSRF handling
│   └── interception.py          # RequestSpy, MockRoute, FailureSimulator
│
├── reports/                     # Generated test reports (gitignored)
├── .auth/                       # Storage state (gitignored)
├── conftest.py                  # Root fixtures
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── .gitignore
```

---

## Key Design Decisions

### 1. Sync API over Async

Python Playwright offers both sync and async APIs. We chose **sync** because:
- Pytest fixtures work naturally with sync code (no `pytest-asyncio` needed)
- Debugging is straightforward — stack traces are linear
- Every page-object method is a simple function call, easy to explain in interviews
- No `async/await` noise cluttering the test code

### 2. Page Objects Instantiated in Tests (Not Fixtures)

The old Python repo had page objects as pytest fixtures, which created hidden dependency chains. We instantiate them explicitly in each test:

```python
def test_booking(self, page, base_url):
    home = HomePage(page, base_url)      # ← visible, traceable
    booking = BookingStep1Page(page, base_url)
```

This makes every test self-documenting — you can see exactly what pages are used.

### 3. Config Singleton

All settings flow through `config.settings` — a single object loaded once at import time. Tests never read `os.environ` directly.

### 4. Global Auth Setup

Authentication runs once per session (not per test), saving ~20 seconds per test. The storage state is saved to `.auth/storageState.json` and loaded by the `auth_context` / `auth_page` fixtures.

### 5. Two-Layer Chat Widget Blocking

Intercom chat widgets are the #1 source of test flakiness. We block them at:
1. **Network level** — `page.route()` aborts requests to chat domains
2. **DOM level** — `MutationObserver` removes elements as they appear

### 6. Scenario-Driven Parameterization

Tests iterate over scenario dicts from `data/test_data.py`. Adding a new test path is a one-line dict addition — no new test code needed.

---

## JS vs Python Implementation Differences

| Aspect | JavaScript (Original) | Python (This Framework) |
|--------|----------------------|------------------------|
| **API** | Async (`await page.click()`) | Sync (`page.click()`) |
| **Test Runner** | `@playwright/test` | `pytest` + `pytest-playwright` |
| **Fixtures** | `test.extend()` | `@pytest.fixture` + `conftest.py` |
| **Assertions** | `expect()` (Playwright) | `expect()` (same API in Python) |
| **Config** | `playwright.config.js` + `dotenv` | `config/settings.py` + `dotenv` |
| **Global Setup** | `globalSetup` function | Session-scoped fixture calling `run_global_setup()` |
| **Typing** | `pressSequentially(text, { delay })` | `press_sequentially(text, delay=50)` |
| **Route Patterns** | JS RegExp (`/intercom\|chat/`) | Glob patterns (`**/intercom/**`) |
| **Try/Catch** | `try { } catch { }` | `try: ... except PlaywrightTimeout: pass` |
| **Date Parsing** | Manual month arrays | `datetime.strptime()` / `strftime()` |
| **Regex Escape** | Manual char replacement | `re.escape()` |
| **Parallel** | `fullyParallel` config flag | `pytest-xdist` (`-n auto`) |
| **Interception** | `route.continue()` | `route.continue_()` (underscore!) |
| **Browser Selection** | `BROWSERS` env → config projects | `BROWSERS` env (pytest-playwright handles it) |

---

## Known Challenges & Solutions

### 1. Focus Stealing by Chat Widgets

**Problem:** Intercom grabs focus mid-typing, causing `fill()` to target the wrong element.

**Solution:** `type_with_focus_guard()` — types text, checks `input_value()`, and if it doesn't match, dismisses the chat widget and retries up to 3 times.

### 2. Autocomplete Timing

**Problem:** Google Places autocomplete only triggers on keyboard events, not programmatic `fill()`.

**Solution:** `type_carefully()` uses `press_sequentially(text, delay=50)` for character-by-character input, then `wait_for_autocomplete()` waits for `[role="listbox"]` to appear.

### 3. Calendar Navigation

**Problem:** The date picker requires clicking "next month" repeatedly to reach the target date.

**Solution:** A loop that reads the current month label, compares to the target, and clicks next. Python version raises `TimeoutError` after 48 clicks (4 years) instead of failing silently like the old code.

### 4. Detached DOM Elements

**Problem:** After adding items, the DOM re-renders and locators become stale.

**Solution:** `select_item_size()` has a try/except that re-queries the locator if the first attempt fails due to detachment.

### 5. Bot Protection (PerfDrive/ShieldSquare)

**Problem:** Ship Sticks uses bot protection that can redirect to a CAPTCHA page.

**Solution:** `assert_loaded()` checks the URL for known bot-protection domains and raises a descriptive `RuntimeError` instead of letting tests fail cryptically.

### 6. Python route() vs JS route()

**Problem:** Python's `route()` callback is synchronous — you cannot use `await` inside it.

**Solution:** All interception handlers (`RequestSpy`, `MockRoute`, `FailureSimulator`) use synchronous `route.fulfill()` / `route.continue_()` / `route.abort()`. The `continue_()` method has a trailing underscore because `continue` is a Python keyword.

### 7. Session Isolation

**Problem:** The old Python repo used session-scoped browser contexts, causing state leakage between tests.

**Solution:** Browser contexts and pages are function-scoped by default (pytest-playwright default). The `auth_context` fixture creates a fresh context per test, loaded from the saved storage state.

---

## Network Interception in Python

Network interception is one of the most significant architectural differences between JS and Python Playwright. Here's what you need to know:

### Key Differences from JavaScript

1. **Synchronous handlers**: Python route handlers run synchronously. You cannot `await` anything inside them.

2. **`continue_()` not `continue()`**: Python reserves `continue` as a keyword, so Playwright uses `continue_()`.

3. **Pattern matching**: Use glob patterns (`**/api/**`) or compiled `re.Pattern` objects — not JS RegExp literals.

4. **One handler per route**: The last registered handler wins. If you register two handlers for the same pattern, only the second one fires.

### Three Interception Patterns

```python
from utils.interception import RequestSpy, MockRoute, FailureSimulator

# 1. SPY — observe without modifying
spy = RequestSpy(page, "**/graphql")
spy.attach()
# ... test actions ...
assert spy.count > 0
assert "createOrder" in spy.last_body
spy.detach()

# 2. MOCK — return canned responses
mock = MockRoute(page, "**/api/v1/pricing", json_body={"price": 0})
mock.attach()
# ... test sees the mocked price ...
mock.detach()

# 3. FAIL — simulate errors
fail = FailureSimulator(page, "**/api/v1/orders", status=500)
fail.attach()
# ... test verifies error handling UI ...
fail.detach()
```

### Network Logging

```python
from utils.network_logger import NetworkLogger

logger = NetworkLogger(page)
logger.start()

# Scoped capture (only during a block)
with logger.scoped("checkout"):
    page.click("#pay")
print(logger.scoped_entries)

# Save full traffic to file
logger.save_to_file("reports/traffic.json")

# Cookie dump for auth debugging
NetworkLogger.dump_cookies(context)
```

---

## Running Tests

### Prerequisites

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Run Modes

```bash
# Run all tests (headless)
pytest

# Run headed (see the browser)
HEADED=true pytest

# Run with slow motion (debugging)
HEADED=true SLOW_MO=300 pytest

# Run in debug mode (Playwright Inspector)
PWDEBUG=1 pytest

# Run specific test file
pytest tests/test_booking.py

# Run specific test
pytest tests/test_booking.py::TestBookingStep1::test_requires_completed_fields_before_proceeding

# Run by marker
pytest -m smoke
pytest -m e2e
pytest -m booking

# Run specific scenarios
SCENARIOS=challenge pytest tests/test_booking.py
SCENARIOS=challenge,two_golf_bags_ground pytest tests/test_booking.py

# Verbose output with print statements
pytest -v -s
```

### Parallel Execution

```bash
# Auto-detect workers (one per CPU core)
pytest -n auto

# Fixed number of workers
pytest -n 4

# Parallel + headed
HEADED=true pytest -n 4
```

---

## Environment Switching

Copy `.env.example` to `.env` and modify:

```bash
cp .env.example .env
```

### Supported Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://app.staging.shipsticks.com` | Target application URL |
| `HEADED` | `false` | Show browser window |
| `SLOW_MO` | `0` | Delay between actions (ms) |
| `TIMEOUT` | `60000` | Global timeout (ms) |
| `BROWSERS` | `chromium` | Browser engine |
| `WORKERS` | `1` | Parallel workers |
| `SCENARIOS` | *(all)* | Comma-separated scenario names |
| `AUTH_EMAIL` | `john@gmail.com` | Login email |
| `AUTH_PASSWORD` | `Password` | Login password |

### Environment Profiles

```bash
# Staging (default)
BASE_URL=https://app.staging.shipsticks.com pytest

# Production (read-only tests)
BASE_URL=https://app.shipsticks.com pytest -m smoke

# Local development
BASE_URL=http://localhost:3000 pytest
```

---

## Reporting

### Playwright HTML Report

```bash
# Tests generate traces on first retry automatically
pytest --tracing=on

# View trace
playwright show-trace test-results/trace.zip
```

### Pytest HTML Report

```bash
pytest --html=reports/report.html --self-contained-html
```

### Allure Reporting (Optional)

```bash
# Run tests with Allure
pytest --alluredir=allure-results

# Generate report
allure serve allure-results
```

---

## Parallel Execution

This framework supports parallel execution via `pytest-xdist`:

```bash
pytest -n auto    # One worker per CPU core
pytest -n 4       # Fixed 4 workers
```

### How It Works

- Each worker gets its own browser instance (pytest-playwright handles this)
- Tests are distributed across workers by file
- Global auth setup runs once (session-scoped fixture)
- Each test gets a fresh browser context (no state leakage)

### Caveats

- Sign-up tests create new users — parallel runs may hit rate limits
- The staging server may throttle concurrent connections
- Bot protection is more likely to trigger with parallel requests

---

## Playwright MCP

This repo includes a project-aware launcher for the official Microsoft Playwright MCP server.

Why this exists:

- it keeps MCP browser sessions aligned with the same `TEST_ENV`, `BASE_URL`, viewport, and launch flags used by the Python suite
- it reuses `.auth/storageState.json` when auth bootstrap succeeds
- it avoids maintaining a second copy of browser settings by hand

Requirements:

- Node.js 18+ with `npx`
- Python dependencies from `requirements.txt`

Run it from the repo root:

```bash
python3 scripts/playwright_mcp.py
```

The launcher will:

1. load repo settings from `config/settings.py`
2. run the existing auth bootstrap from `fixtures/global_setup.py`
3. generate `.mcp/playwright.config.json`
4. start `npx @playwright/mcp@latest --config .mcp/playwright.config.json`

Examples:

```bash
TEST_ENV=staging python3 scripts/playwright_mcp.py
```

```bash
BASE_URL=https://www.shipsticks.com HEADED=true python3 scripts/playwright_mcp.py
```

```bash
python3 scripts/playwright_mcp.py --port 8931
```

If you want Codex to use this project-specific launcher instead of raw `npx`, add this to `~/.codex/config.toml`:

```toml
[mcp_servers.playwright]
command = "python3"
args = ["/Users/mustafasapple/RXTesting/shipsticks-python-framework/scripts/playwright_mcp.py"]
```

---

## Extending the Framework

### Adding a New Page Object

1. Create `pages/new_page.py`:
```python
from pages.base_page import BasePage
from playwright.sync_api import expect

class NewPage(BasePage):
    def __init__(self, page, base_url=""):
        super().__init__(page, base_url)
        self.heading = page.get_by_role("heading", name="New Page")

    def assert_loaded(self):
        expect(self.heading).to_be_visible(timeout=15000)
```

2. Use it in a test:
```python
from pages.new_page import NewPage

def test_new_feature(self, page, base_url):
    new_page = NewPage(page, base_url)
    new_page.assert_loaded()
```

### Adding a New Scenario

Add a dict to `data/test_data.py`:
```python
SCENARIOS["new_scenario"] = {
    "shipment_type": "One-way",
    "origin": "...",
    "destination": "...",
    "items": [{"category": "Luggage", "quantity": 1, "sizes": ["Checked"]}],
    "service_level": "Next Day Express",
    "delivery_date": "Friday, June 12, 2026",
}
```

Tests automatically pick it up — no test code changes needed.

### Adding a New Interception Pattern

```python
from utils.interception import MockRoute

class PricingMock(MockRoute):
    """Pre-configured mock for the pricing API."""
    def __init__(self, page, price=0):
        super().__init__(page, "**/api/v1/pricing", json_body={"price": price})
```

---

## Interview Talking Points

### Architecture & Design
- **"Why Page Object Model?"** — Encapsulates UI structure so test logic reads like business requirements. When the UI changes, we fix one page object, not 50 tests.
- **"Why not async?"** — Sync API keeps stack traces readable, avoids `pytest-asyncio` complexity, and Playwright's sync wrapper is thread-safe.
- **"Why explicit page instantiation?"** — Makes dependencies visible. A reader can scan the test and know exactly which pages are involved without tracing fixture chains.

### Anti-Flake Patterns
- **Focus guard** — Retries typing when chat widgets steal focus. This is a real production problem, not academic.
- **Two-layer widget blocking** — Network abort + DOM MutationObserver. Belt and suspenders.
- **Calendar loop safety** — Raises `TimeoutError` after 48 iterations instead of silently failing.
- **Detached element retry** — Re-queries locators when the DOM re-renders during interaction.

### Network Interception
- **"How does interception differ in Python?"** — Sync handlers, `continue_()` underscore, glob patterns instead of RegExp. I built three utility classes (`RequestSpy`, `MockRoute`, `FailureSimulator`) that hide these differences.
- **"When would you use a spy vs a mock?"** — Spy for validation (did the app call the right API?), mock for isolation (test UI behavior without backend), failure sim for resilience testing.

### Testing Strategy
- **Scenario-driven parameterization** — Adding a test path is a dict, not code. Scales to dozens of variations without test bloat.
- **Global auth setup** — Login once, save cookies, reuse across all tests. Saves ~20s per test.
- **Bot protection guardrail** — Explicit error message instead of cascading locator failures.

### Technical Depth
- **Storage state** — Playwright serializes cookies + localStorage to JSON. We load it into fresh contexts for pre-authenticated tests.
- **CSRF handling** — The `APIHelper` extracts the token from a `<meta>` tag and attaches it to subsequent API calls.
- **Config singleton** — All runtime settings in one object. Environment switching is a `.env` file change, not a code change.

---

## Quick Reference

```bash
# Setup
pip install -r requirements.txt && playwright install chromium

# Run all tests
pytest

# Run headed with slow motion
HEADED=true SLOW_MO=300 pytest

# Run specific scenario
SCENARIOS=challenge pytest tests/test_booking.py

# Run smoke tests in parallel
pytest -m smoke -n auto

# Debug with Playwright Inspector
PWDEBUG=1 pytest tests/test_login.py

# Generate HTML report
pytest --html=reports/report.html --self-contained-html
```
