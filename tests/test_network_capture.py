"""Capture the main UI flows to a JSON file, matching the JS repo's utility test."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from data.test_data import SCENARIOS, get_sign_up_data
from pages.booking_step1_page import BookingStep1Page
from pages.home_page import HomePage

OUT_FILE = Path(__file__).resolve().parent.parent / "tmp" / "network-capture-python.json"


def _is_api_call(url: str) -> bool:
    ignored_extensions = (".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".map")
    ignored_vendors = ("google-analytics", "intercom", "hotjar", "segment")
    return not url.endswith(ignored_extensions) and not any(vendor in url for vendor in ignored_vendors)


def _save_capture(key: str, entries: list[dict]) -> None:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if OUT_FILE.exists():
        try:
            data = json.loads(OUT_FILE.read_text())
        except json.JSONDecodeError:
            data = {}
    data[key] = entries
    OUT_FILE.write_text(json.dumps(data, indent=2))


@pytest.mark.network
class TestNetworkCapture:
    def test_capture_sign_up_flow(self, page, base_url):
        log_entries: list[dict] = []
        sign_up = get_sign_up_data()

        def on_request(request):
            if _is_api_call(request.url):
                log_entries.append(
                    {
                        "dir": "REQ",
                        "method": request.method,
                        "url": request.url,
                        "postData": request.post_data,
                    }
                )

        def on_response(response):
            if not _is_api_call(response.url):
                return
            body = None
            try:
                body = response.json()
            except Exception:
                try:
                    body = response.text()[:800]
                except Exception:
                    body = None
            log_entries.append(
                {
                    "dir": "RES",
                    "method": response.request.method,
                    "url": response.url,
                    "status": response.status,
                    "body": body,
                }
            )

        page.on("request", on_request)
        page.on("response", on_response)

        home = HomePage(page, base_url)
        home.goto()
        home.click_sign_in()
        home.assert_sign_in_modal_visible()
        home.switch_to_sign_up()
        home.assert_sign_up_modal_visible()
        home.fill_sign_up_form(sign_up)
        home.click_continue_to_create_password()
        home.fill_password_fields(sign_up["password"])
        home.skip_verify_your_number()
        home.assert_logged_in(sign_up["first_name"])

        _save_capture("sign_up_flow", log_entries)

    def test_capture_booking_step1_flow(self, page, base_url):
        log_entries: list[dict] = []

        def on_request(request):
            if _is_api_call(request.url):
                log_entries.append(
                    {
                        "dir": "REQ",
                        "method": request.method,
                        "url": request.url,
                        "postData": request.post_data,
                    }
                )

        def on_response(response):
            if not _is_api_call(response.url):
                return
            body = None
            try:
                body = response.json()
            except Exception:
                try:
                    body = response.text()[:800]
                except Exception:
                    body = None
            log_entries.append(
                {
                    "dir": "RES",
                    "method": response.request.method,
                    "url": response.url,
                    "status": response.status,
                    "body": body,
                }
            )

        page.on("request", on_request)
        page.on("response", on_response)

        home = HomePage(page, base_url)
        booking = BookingStep1Page(page, base_url)
        scenario = SCENARIOS["challenge"]

        home.goto()
        home.start_quote(
            shipment_type=scenario["shipment_type"],
            origin=scenario["origin"],
            destination=scenario["destination"],
        )
        booking.assert_loaded()
        booking.dismiss_weather_warning_if_present()
        booking.configure_items(booking.get_challenge_items(scenario))
        booking.select_delivery_date(scenario["delivery_date"])
        booking.select_shipping_method(scenario["service_level"])
        booking.proceed_to_next_step()

        _save_capture("booking_step1_flow", log_entries)
