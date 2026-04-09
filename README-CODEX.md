# Ship Sticks Python Framework Guide

This file explains the Python Playwright framework in `/Users/mustafasapple/RXTesting/shipsticks-python-framework` using the actual code in this repo. It is written for someone who already understands JavaScript automation better than Python.

## What This Repo Does

The Python repo mirrors the JavaScript repo’s main framework behavior:

- page objects for the booking flow
- scenario-driven test data
- session auth saved to `.auth/storageState.json`
- network interception and mocking
- API user creation helpers
- booking, login, E2E, interception, and capture tests

The main difference is the runner:

- JS uses `@playwright/test`
- Python uses `pytest` + `pytest-playwright`

## Folder Structure

- `config/settings.py`
  Loads all runtime settings from env vars. This is the single config source for Python.
- `conftest.py`
  Central fixture hub. It defines `base_url`, API context fixtures, authenticated browser fixtures, and default page timeouts.
- `fixtures/global_setup.py`
  Runs one authenticated API login before the suite and writes `.auth/storageState.json`.
- `data/test_data.py`
  Holds scenarios, login/sign-up/payment data, variations, and helper functions like `get_sign_up_data()`.
- `pages/base_page.py`
  Shared anti-flake layer: careful typing, focus guard, chat-widget blocking, cookie handling, autocomplete waits.
- `pages/home_page.py`
  Homepage quote widget plus sign-in/sign-up flow.
- `pages/booking_step1_page.py`
  Step 1 booking page: addresses, dates, items, shipping methods, anti-bot detection.
- `pages/booking_login_page.py`
  Login barrier page and order-summary assertions.
- `pages/travelers_page.py`
  Traveler-details checks.
- `pages/payment_page.py`
  Coverage, pickup method, billing country, card entry.
- `pages/review_page.py`
  Final review assertions.
- `pages/order_confirmation_page.py`
  Final success-page assertion.
- `utils/api_helpers.py`
  API helper wrapper for CSRF handling, user creation, GraphQL calls, and Devise login.
- `utils/create_user.py`
  Python equivalent of the JS `utils/createUser.js`. Supports UI and API account creation.
- `utils/interception.py`
  Generic request spy, canned mocks, failure simulation, and GraphQL operation interception.
- `utils/network_logger.py`
  Python equivalent of the JS network logger utilities.
- `tests/test_booking.py`
  Step 1 happy path by scenario.
- `tests/test_booking_blocking.py`
  Detects PerfDrive/ShieldSquare bot-protection redirects.
- `tests/test_login.py`
  Full sign-up flow through UI.
- `tests/test_e2e.py`
  Full user journey from sign-up to order confirmation.
- `tests/test_api_interception.py`
  App-specific route mocking and GraphQL interception parity with the JS repo.
- `tests/test_api_user.py`
  `/api/v5/users` coverage.
- `tests/test_create_user.py`
  UI/API user creation coverage.
- `tests/test_network_capture.py`
  Writes request/response capture output to `tmp/network-capture-python.json`.
- `tests/test_network_interception.py`
  Lower-level utility tests for interception classes.

## How Fixtures Work

The fixtures live in [`conftest.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/conftest.py).

- `_global_auth_setup`
  Session-scoped and autouse. Runs once before tests and calls `run_global_setup()`.
- `browser_type_launch_args`
  Passes browser launch args like `headless`, `slow_mo`, and Chromium flags.
- `browser_context_args`
  Sets viewport and `ignore_https_errors`.
- `base_url`
  Exposes the chosen app URL to tests.
- `_configure_page_defaults`
  Applies default timeout and navigation timeout to every test page.
- `api_context`
  Fresh Playwright API request context targeting the web host used for login/API calls.
- `authenticated_api_context`
  API context preloaded with saved storage state.
- `auth_context`
  Browser context that loads `.auth/storageState.json`.
- `auth_page`
  Page created from `auth_context`.

Python does not use JS-style `test.extend()`. In pytest, fixtures are injected as function arguments:

```python
def test_create_user_via_api(self, api_context, base_url):
    ...
```

## How Config Works

All config comes from [`config/settings.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/config/settings.py).

Supported environment variables:

- `TEST_ENV`
- `BASE_URL`
- `AUTH_EMAIL`
- `AUTH_PASSWORD`
- `HEADED`
- `SLOW_MO`
- `TIMEOUT`
- `WORKERS`
- `FULLY_PARALLEL`
- `VERBOSE`
- `BROWSERS`
- `SCENARIOS`
- `PROD_EMAIL`
- `PROD_PASSWORD`

Resolution order:

1. If `BASE_URL` is set, Python uses it.
2. Otherwise `TEST_ENV=staging` resolves to `https://app.staging.shipsticks.com`.
3. `TEST_ENV=prod` resolves to `https://www.shipsticks.com`.

The settings file also derives `web_base_url`. That matters because the app UI runs on `app...`, but auth/API login in this framework uses the `www.app...` host just like the JS global setup.

## How Environments and Base URL Switching Work

Examples:

```bash
cd /Users/mustafasapple/RXTesting/shipsticks-python-framework
pytest
```

```bash
cd /Users/mustafasapple/RXTesting/shipsticks-python-framework
BASE_URL=https://app.staging.shipsticks.com pytest
```

```bash
cd /Users/mustafasapple/RXTesting/shipsticks-python-framework
TEST_ENV=prod BASE_URL=https://www.shipsticks.com pytest tests/test_booking.py
```

If you point the framework at an `app.` host, auth setup automatically switches the login/API host to `www.app.` internally.

## How Auth and Storage State Work

Auth setup lives in [`fixtures/global_setup.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/fixtures/global_setup.py).

It does not log in through the UI. It follows the same pattern as the JS repo:

1. `GET /users/sign_in`
2. Read the CSRF token from the page HTML
3. `POST /users/sign_in` with form-encoded credentials
4. Save storage state to `.auth/storageState.json`

Why this matters:

- it is faster than clicking through the login modal
- it is less flaky than UI login for suite setup
- authenticated fixtures can reuse the saved session

## How Page Objects Work

Each page object is a Python class with a constructor that receives `page` and sometimes `base_url`.

Example:

```python
home = HomePage(page, base_url)
booking = BookingStep1Page(page, base_url)
```

The flow is the same idea as JS, just with snake_case names:

- JS `clickSignIn()` -> Python `click_sign_in()`
- JS `selectDeliveryDate()` -> Python `select_delivery_date()`
- JS `skipVerifyYourNumber()` -> Python `skip_verify_your_number()`

The anti-flake behavior is mostly centralized in [`pages/base_page.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/pages/base_page.py):

- `type_carefully()`
- `type_with_focus_guard()`
- `wait_for_autocomplete()`
- `dismiss_chat_widget_if_present()`
- `accept_cookies_if_present()`

## Helpers and Utilities

Important helper modules:

- [`utils/create_user.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/utils/create_user.py)
  Creates users either through UI or API.
- [`utils/api_helpers.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/utils/api_helpers.py)
  Gives you `create_user()`, `graphql()`, and `login_via_devise()`.
- [`utils/interception.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/utils/interception.py)
  Gives you `RequestSpy`, `MockRoute`, `FailureSimulator`, and `GraphQLInterceptor`.
- [`utils/network_logger.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/utils/network_logger.py)
  Gives you `with_network_logging()`, `attach_network_logging()`, and `dump_cookies()`.

## Interception and Mocking in Python Playwright

The app-specific interception examples are in [`tests/test_api_interception.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/tests/test_api_interception.py).

That file covers the same major ideas as the JS repo:

- capturing `GetDeliverByTransitRates` request payloads
- mocking empty shipping rates
- mocking server errors
- mocking multiple transit-rate options
- intercepting registration failures

Python-specific differences:

- route handlers are synchronous
- you call `route.continue_()` instead of `route.continue()`
- regex handling uses Python `re`
- pytest does not have Playwright Test’s exact `expect.poll` API, so retry logic is usually explicit

## How to Run Tests

From the Python repo root:

```bash
cd /Users/mustafasapple/RXTesting/shipsticks-python-framework
pip install -r requirements.txt
playwright install chromium
pytest
```

Run only booking tests:

```bash
pytest tests/test_booking.py
```

Run one scenario:

```bash
SCENARIOS=challenge pytest tests/test_booking.py
```

Run API-only coverage:

```bash
pytest tests/test_api_user.py tests/test_create_user.py
```

## Playwright MCP In This Repo

This repo includes a Python launcher at [`scripts/playwright_mcp.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/scripts/playwright_mcp.py).

Use it when you want the official Microsoft Playwright MCP server to inherit this framework's Python-side config instead of starting with generic defaults.

What it does:

- loads `TEST_ENV`, `BASE_URL`, viewport, browser choice, and launch flags from [`config/settings.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/config/settings.py)
- runs the existing auth bootstrap from [`fixtures/global_setup.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/fixtures/global_setup.py)
- writes a generated config file to `.mcp/playwright.config.json`
- launches `npx @playwright/mcp@latest --config ...`

Run it from the repo root:

```bash
python3 scripts/playwright_mcp.py
```

Examples:

```bash
TEST_ENV=staging python3 scripts/playwright_mcp.py
```

```bash
BASE_URL=https://www.shipsticks.com HEADED=true python3 scripts/playwright_mcp.py --port 8931
```

## Headed, Debug, Parallel, and Reporting

Headed:

```bash
HEADED=true pytest
```

Debug:

```bash
PWDEBUG=1 HEADED=true pytest -s tests/test_login.py
```

Slow motion:

```bash
HEADED=true SLOW_MO=300 pytest tests/test_booking.py
```

Parallel with `pytest-xdist`:

```bash
pytest -n 4
```

HTML report with `pytest-html`:

```bash
pytest --html=reports/pytest-report.html --self-contained-html
```

The repo keeps plugin-specific reporting out of default `pytest.ini` so collection still works even if optional plugins are not installed yet.

## How This Python Repo Compares to the JS Repo

Parity areas now covered:

- page objects
- booking scenarios
- API user creation
- UI user creation helper
- auth/session reuse
- GraphQL interception tests
- network capture output
- environment switching through env vars

Main unavoidable differences:

- pytest fixture injection instead of Playwright Test fixtures
- snake_case method names instead of camelCase
- no exact Playwright Test UI mode equivalent in Python pytest

## Common Beginner Confusion Points

- `page` is the active browser tab from the pytest-playwright plugin.
- `context` is the browser context. Cookies/storage state live there.
- `base_url` is injected by fixture, not imported directly from settings in most tests.
- `auth_context` is not the same thing as `api_context`.
- `storage_state.json` is just saved browser/session state. It is not a custom framework format.
- `route.continue_()` has an underscore because `continue` is a Python keyword.
- Many Python methods look similar to JS, but Playwright Python uses sync calls by default in this repo.

## How to Extend the Framework Safely

If you add a new flow:

1. Put stable data in [`data/test_data.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/data/test_data.py).
2. Add locators and behavior to the relevant page object.
3. Reuse `BasePage` helpers instead of duplicating waits.
4. If the new flow uses API setup, add it to [`utils/api_helpers.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/utils/api_helpers.py) or [`utils/create_user.py`](/Users/mustafasapple/RXTesting/shipsticks-python-framework/utils/create_user.py).
5. If you need mocking, prefer operation-specific interception instead of broad catch-all mocks.
6. Add at least one scenario-focused test and one negative/interception test if the UI depends on network behavior.
