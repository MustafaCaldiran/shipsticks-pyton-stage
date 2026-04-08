"""User-creation helpers ported from the JavaScript repo."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from playwright.sync_api import sync_playwright

from data.test_data import get_sign_up_data
from pages.home_page import HomePage
from utils.api_helpers import APIHelper

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext, Page


def create_user_via_api(
    base_url: str,
    request_context: "APIRequestContext | None" = None,
    sign_up_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sign_up = sign_up_data or get_sign_up_data()

    if request_context is not None:
        helper = APIHelper(request_context, base_url)
        body = helper.create_user(
            email=sign_up["email"],
            password=sign_up["password"],
            first_name=sign_up["firstName"],
            last_name=sign_up["lastName"],
            phone_number=sign_up["phoneNumber"],
            hear_about_us=sign_up["howDidYouHear"],
        )
    else:
        with sync_playwright() as playwright:
            context = playwright.request.new_context(
                base_url=base_url,
                ignore_https_errors=True,
            )
            helper = APIHelper(context, base_url)
            body = helper.create_user(
                email=sign_up["email"],
                password=sign_up["password"],
                first_name=sign_up["firstName"],
                last_name=sign_up["lastName"],
                phone_number=sign_up["phoneNumber"],
                hear_about_us=sign_up["howDidYouHear"],
            )
            context.dispose()

    return {
        "id": body.get("id"),
        "email": body["email"],
        "password": sign_up["password"],
        "firstName": body.get("first_name", sign_up["firstName"]),
        "lastName": body.get("last_name", sign_up["lastName"]),
        "phoneNumber": body.get("phone_number", sign_up["phoneNumber"]),
        "authToken": body.get("auth_token", ""),
    }


def create_user_via_ui(
    page: "Page",
    base_url: str,
    sign_up_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    home = HomePage(page, base_url)
    sign_up = sign_up_data or get_sign_up_data()

    home.goto()
    home.click_sign_in()
    home.assert_sign_in_modal_visible()
    home.switch_to_sign_up()
    home.assert_sign_up_modal_visible()
    home.fill_sign_up_form(sign_up)
    home.click_continue_to_create_password()
    home.fill_password_fields(sign_up["password"])
    home.skip_verify_your_number()
    home.assert_logged_in(sign_up["firstName"])

    return {**sign_up, "homePage": home}


def save_created_users(file_path: str | Path, base_url: str, created: list[dict], failed: list[dict]) -> None:
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"Created: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"Environment: {base_url}",
        f"Total: {len(created)} created, {len(failed)} failed",
        "",
        "#   Email                              Password",
        "─" * 66,
        *[
            f"{str(item['index']).rjust(2)}  {item['user']['email'].ljust(35)}  {item['user']['password']}"
            for item in created
        ],
    ]
    if failed:
        lines.extend(["", "Failed:", *[f"  [{item['index']}] {item['error']}" for item in failed]])
    output_path.write_text("\n".join(lines) + "\n")
