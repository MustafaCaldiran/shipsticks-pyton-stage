from __future__ import annotations

from pathlib import Path

import pytest

from data.test_data import SCENARIOS, get_sign_up_data
from pages.booking_step1_page import BookingStep1Page
from pages.home_page import HomePage
from utils.network_capture import save_network_capture, with_network_capture

OUT_FILE = Path(__file__).resolve().parent.parent / "tmp" / "network-capture.json"


@pytest.mark.network
class TestNetworkCapture:
    def test_capture_sign_up_flow(self, page, base_url):
        home = HomePage(page, base_url)
        sign_up = get_sign_up_data()

        log = with_network_capture(
            page,
            lambda: (
                home.goto(),
                home.click_sign_in(),
                home.assert_sign_in_modal_visible(),
                home.switch_to_sign_up(),
                home.assert_sign_up_modal_visible(),
                home.fill_sign_up_form(sign_up),
                home.click_continue_to_create_password(),
                home.fill_password_fields(sign_up["password"]),
                home.skip_verify_your_number(),
                home.assert_logged_in(sign_up["firstName"]),
            ),
        )
        save_network_capture(OUT_FILE, "sign_up_flow", log)

    def test_capture_booking_step_1_flow(self, page, base_url):
        home = HomePage(page, base_url)
        booking = BookingStep1Page(page, base_url)
        scenario = SCENARIOS["challenge"]

        log = with_network_capture(
            page,
            lambda: (
                home.goto(),
                home.start_quote(
                    shipment_type=scenario["shipmentType"],
                    origin=scenario["origin"],
                    destination=scenario["destination"],
                ),
                booking.assert_loaded(),
                booking.dismiss_weather_warning_if_present(),
                booking.configure_items(booking.get_challenge_items(scenario)),
                booking.select_delivery_date(scenario["deliveryDate"]),
                booking.select_shipping_method(scenario["serviceLevel"]),
                booking.proceed_to_next_step(),
            ),
        )
        save_network_capture(OUT_FILE, "booking_step1_flow", log)
