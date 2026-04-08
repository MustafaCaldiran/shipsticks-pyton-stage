"""Python equivalents of the JavaScript create-user coverage."""

from __future__ import annotations

import pytest

from data.test_data import get_sign_up_data
from utils.create_user import create_user_via_api, create_user_via_ui
from utils.network_logger import dump_cookies, with_network_logging


@pytest.mark.api
class TestCreateUser:
    def test_create_user_via_ui_with_network_capture(self, page, context, base_url):
        user = {}
        with with_network_logging(page, "SIGN-UP"):
            user = create_user_via_ui(page, base_url)

        cookies = dump_cookies(context, "AFTER SIGN-UP")
        assert user["email"]
        assert user["first_name"] == "John"
        assert isinstance(cookies, list)

    def test_create_user_via_api(self, api_context, base_url):
        user = create_user_via_api(base_url, api_context, get_sign_up_data())
        assert user["id"]
        assert user["email"]
        assert user["auth_token"] is not None
