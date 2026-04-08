"""
Booking Step 1 — happy path tests.

Dynamically parameterized: one test case per scenario in test_data.SCENARIOS.
Filter at runtime with: SCENARIOS=challenge pytest tests/test_booking.py

Architecture:
  - Each test instantiates its own page objects (explicit dependency chain)
  - Scenarios flow through pytest.mark.parametrize for parallel-friendly IDs
  - The "requires completed fields" test is a standalone negative check
"""

import os

import pytest
from playwright.sync_api import expect

from data.test_data import SCENARIOS, get_scenario_entries
from pages.home_page import HomePage
from pages.booking_step1_page import BookingStep1Page
from pages.booking_login_page import BookingLoginPage

# ---------------------------------------------------------------------------
# Scenario parameterization
# ---------------------------------------------------------------------------

_selected = [s.strip() for s in os.environ.get("SCENARIOS", "").split(",") if s.strip()]
_scenario_entries = get_scenario_entries(_selected or None)


@pytest.mark.booking
class TestBookingStep1:
    """Ship Sticks Booking Step 1 — scenario-driven tests."""

    @pytest.mark.parametrize(
        "scenario_name, scenario",
        _scenario_entries,
        ids=[name for name, _ in _scenario_entries],
    )
    def test_completes_step1_happy_path(self, page, base_url, scenario_name, scenario):
        """
        Full Step 1 happy path: quote → items → date → shipping → summary.

        Verifies the order summary on the login page matches the scenario.
        """
        home = HomePage(page, base_url)
        booking = BookingStep1Page(page, base_url)
        login_page = BookingLoginPage(page)

        # 1. Navigate and complete quote widget
        home.goto()
        home.start_quote(
            shipment_type=scenario["shipment_type"],
            origin=scenario["origin"],
            destination=scenario["destination"],
        )

        # 2. Configure Step 1
        booking.assert_loaded()
        booking.dismiss_weather_warning_if_present()

        challenge_items = BookingStep1Page.get_challenge_items(scenario)
        booking.configure_items(challenge_items)
        booking.select_delivery_date(scenario["delivery_date"])
        booking.select_shipping_method(scenario["service_level"])

        # 3. Proceed to next step
        booking.proceed_to_next_step()

        # 4. Verify order summary
        login_page.assert_loaded()

        # Build item labels for summary verification
        item_labels = []
        for item in challenge_items:
            for idx, size in enumerate(item["sizes"]):
                item_labels.append(
                    BookingLoginPage.build_summary_item_label(
                        item["category"], size, idx + 1
                    )
                )

        login_page.assert_summary_matches_challenge(
            delivery_date=scenario["delivery_date"],
            origin=scenario["origin"],
            destination=scenario["destination"],
            items=item_labels,
        )

    def test_requires_completed_fields_before_proceeding(self, page, base_url):
        """Get Started button should be disabled when addresses are empty."""
        home = HomePage(page, base_url)
        home.goto()

        expect(home.get_started_button).to_be_disabled()
        expect(home.origin_field).to_be_visible()
