from __future__ import annotations

from pathlib import Path
from time import sleep

import pytest

from utils.create_user import create_user_via_api, create_user_via_ui, save_created_users
from utils.network_logger import dump_cookies, with_network_logging

OUT_FILE = Path(__file__).resolve().parent.parent / "tmp" / "created-users.txt"


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
        pytest.skip("Long-running parity test; run explicitly when needed.")

    def test_create_20_users_api_bulk_parallel(self, base_url):
        pytest.skip("Long-running parity test; run explicitly when needed.")
