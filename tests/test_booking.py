from __future__ import annotations

import os

import pytest
from playwright.sync_api import expect

from data.test_data import get_scenario_entries
from pages.booking_login_page import BookingLoginPage
from pages.booking_step1_page import BookingStep1Page
from pages.home_page import HomePage

selected_scenario_names = [
    name.strip()
    for name in os.environ.get("SCENARIOS", "").split(",")
    if name.strip()
]


@pytest.mark.booking
class TestBookingStep1:
    @pytest.mark.parametrize(
        "scenario_name, scenario",
        get_scenario_entries(selected_scenario_names),
        ids=[name for name, _ in get_scenario_entries(selected_scenario_names)],
    )
    def test_completes_step1_happy_path(self, page, base_url, scenario_name, scenario):
        home_page = HomePage(page, base_url)
        booking_page = BookingStep1Page(page, base_url)
        login_page = BookingLoginPage(page)

        home_page.goto()
        home_page.start_quote(
            shipment_type=scenario["shipmentType"],
            origin=scenario["origin"],
            destination=scenario["destination"],
        )
        booking_page.assert_loaded()
        booking_page.dismiss_weather_warning_if_present()

        challenge_items = booking_page.get_challenge_items(scenario)
        booking_page.configure_items(challenge_items)
        booking_page.select_delivery_date(scenario["deliveryDate"])
        booking_page.select_shipping_method(scenario["serviceLevel"])

        booking_page.proceed_to_next_step()
        login_page.assert_loaded()
        login_page.assert_summary_matches_challenge(
            delivery_date=scenario["deliveryDate"],
            origin=scenario["origin"],
            destination=scenario["destination"],
            items=[
                login_page.build_summary_item_label(item["category"], size, index + 1)
                for item in challenge_items
                for index, size in enumerate(item["sizes"])
            ],
        )

    def test_requires_completed_fields_before_moving_to_traveler_details(self, page, base_url):
        home_page = HomePage(page, base_url)

        home_page.goto()
        expect(home_page.get_started_button).to_be_disabled()
        expect(home_page.origin_field).to_be_visible()
