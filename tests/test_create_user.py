from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
import requests

from utils.create_user import create_user_via_api, create_user_via_ui, save_created_users
from utils.network_logger import dump_cookies, with_network_logging
from data.test_data import get_sign_up_data

OUT_FILE = Path(__file__).resolve().parent.parent / "tmp" / "created-users.txt"

# Override via env: BULK_COUNT=50 pytest tests/test_create_user.py
BULK_COUNT = int(os.getenv("BULK_COUNT", "20"))
# Max concurrent threads for parallel mode. Override via BULK_WORKERS=10
BULK_WORKERS = int(os.getenv("BULK_WORKERS", "5"))


def _create_one_user(base_url: str, index: int) -> dict:
    """Create a single user via direct HTTP POST (no Playwright context needed)."""
    sign_up = get_sign_up_data()
    payload = {
        "user": {
            "email": sign_up["email"],
            "password": sign_up["password"],
            "password_confirmation": sign_up["password"],
            "first_name": sign_up["firstName"],
            "last_name": sign_up["lastName"],
            "phone_number": f"+1 {sign_up['phoneNumber']}",
            "country_code": "us",
            "hear_about_us": sign_up["howDidYouHear"],
            "other_hear_about_us": "",
            "terms": True,
            "mobile_verified": False,
            "brand_id": "shipsticks",
            "sms_tracking_optin": False,
        },
        "frontend_app_booking_flow": True,
    }
    resp = requests.post(
        f"{base_url}/api/v5/users",
        json=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        verify=False,
        timeout=30,
    )
    assert resp.ok, f"create_user failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    return {
        "index": index,
        "user": {
            "email": sign_up["email"],
            "password": sign_up["password"],
            "id": body.get("id"),
        },
    }


@pytest.mark.api
class TestCreateUser:
    def test_create_user_ui_flow_with_network_capture(self, page, context, base_url):
        captured_requests = []

        def on_request(request):
            if "shipsticks" not in request.url or request.method != "POST":
                return
            body = request.post_data
            if body:
                captured_requests.append({"url": request.url, "body": body})

        page.on("request", on_request)
        with with_network_logging(page, "SIGN-UP"):
            user = create_user_via_ui(page, base_url)

        cookies = dump_cookies(context, "AFTER SIGN-UP")
        assert user["email"]
        assert user["firstName"]
        assert user["lastName"]
        assert captured_requests
        assert isinstance(cookies, list)

    def test_create_user_api_only(self, api_context, base_url):
        user = create_user_via_api(base_url, api_context)
        assert user["id"]
        assert user["email"]
        assert user["firstName"]
        assert user["authToken"] is not None

    def test_create_20_users_api_bulk_sequential(self, base_url):
        created, failed = [], []
        for i in range(1, BULK_COUNT + 1):
            try:
                result = _create_one_user(base_url, i)
                created.append(result)
                print(f"[{i}/{BULK_COUNT}] created {result['user']['email']}")
            except Exception as exc:
                failed.append({"index": i, "error": str(exc)})
                print(f"[{i}/{BULK_COUNT}] FAILED: {exc}")

        save_created_users(OUT_FILE, base_url, created, failed)
        print(f"\nDone: {len(created)} created, {len(failed)} failed → {OUT_FILE}")
        assert len(created) > 0, "No users were created"
        assert len(failed) == 0, f"{len(failed)} user(s) failed: {failed}"

    def test_create_20_users_api_bulk_parallel(self, base_url):
        created, failed = [], []
        with ThreadPoolExecutor(max_workers=BULK_WORKERS) as pool:
            futures = {
                pool.submit(_create_one_user, base_url, i): i
                for i in range(1, BULK_COUNT + 1)
            }
            for future in as_completed(futures):
                i = futures[future]
                try:
                    result = future.result()
                    created.append(result)
                    print(f"[{i}] created {result['user']['email']}")
                except Exception as exc:
                    failed.append({"index": i, "error": str(exc)})
                    print(f"[{i}] FAILED: {exc}")

        save_created_users(OUT_FILE, base_url, created, failed)
        print(f"\nDone: {len(created)} created, {len(failed)} failed → {OUT_FILE}")
        assert len(created) > 0, "No users were created"
        assert len(failed) == 0, f"{len(failed)} user(s) failed: {failed}"
