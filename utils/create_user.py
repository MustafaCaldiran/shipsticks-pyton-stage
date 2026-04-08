"""User-creation helpers mirrored from the JavaScript framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from data.test_data import get_sign_up_data
from pages.home_page import HomePage
from utils.api_helpers import APIHelper

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext, Page


def create_user_via_api(
    base_url: str,
    request_context: "APIRequestContext",
    sign_up_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a user with POST /api/v5/users and return the normalized payload."""
    sign_up = sign_up_data or get_sign_up_data()
    helper = APIHelper(request_context, base_url.replace("://app.", "://www.app."))
    body = helper.create_user(
        email=sign_up["email"],
        password=sign_up["password"],
        first_name=sign_up["first_name"],
        last_name=sign_up["last_name"],
        phone_number=sign_up["phone_number"],
        hear_about_us=sign_up["how_did_you_hear"],
    )

    return {
        "id": body.get("id") or body.get("_id") or body.get("user", {}).get("id"),
        "email": body["email"],
        "password": sign_up["password"],
        "first_name": body.get("first_name", sign_up["first_name"]),
        "last_name": body.get("last_name", sign_up["last_name"]),
        "phone_number": body.get("phone_number", sign_up["phone_number"]),
        "auth_token": body.get("auth_token", ""),
    }


def create_user_via_ui(
    page: "Page",
    base_url: str,
    sign_up_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Drive the full sign-up UI flow and return the created user data."""
    sign_up = sign_up_data or get_sign_up_data()
    home_page = HomePage(page, base_url)

    home_page.goto()
    home_page.click_sign_in()
    home_page.assert_sign_in_modal_visible()
    home_page.switch_to_sign_up()
    home_page.assert_sign_up_modal_visible()
    home_page.fill_sign_up_form(sign_up)
    home_page.click_continue_to_create_password()
    home_page.fill_password_fields(sign_up["password"])
    home_page.skip_verify_your_number()
    home_page.assert_logged_in(sign_up["first_name"])

    return {
        **sign_up,
        "home_page": home_page,
    }
