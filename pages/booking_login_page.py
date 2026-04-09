"""
BookingLoginPage — the auth barrier between Step 1 and Travelers.

Also contains the order summary sidebar verification logic.
Uses datetime for date formatting instead of manual month/weekday arrays.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from playwright.sync_api import expect, Error as PlaywrightError, TimeoutError as PlaywrightTimeout

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class BookingLoginPage(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        self.login_heading = page.get_by_role("heading", name="Account Login")
        self.order_summary_heading = page.get_by_role("heading", name="Order Summary")
        self.summary_shipment_date = page.locator('[aria-label="ShipmentDate"]').last
        self.summary_shipment_cities = page.locator('[aria-label="ShipmentCity"]')
        self.summary_payment_items = page.locator('[aria-label="PaymentSummaryItem"]')

    # ==================================================================
    # Assertions
    # ==================================================================

    def assert_loaded(self) -> None:
        assert "/book/login" in self.page.url, f"Expected /book/login in URL, got {self.page.url}"
        expect(self.login_heading).to_be_visible(timeout=15000)

    # ==================================================================
    # Summary data extraction
    # ==================================================================

    def get_summary_shipment_date_text(self) -> str:
        return self.summary_shipment_date.text_content().strip()

    def get_summary_origin_city_text(self) -> str:
        return self.summary_shipment_cities.nth(0).text_content().strip()

    def get_summary_destination_city_text(self) -> str:
        return self.summary_shipment_cities.nth(1).text_content().strip()

    # ==================================================================
    # Summary assertions
    # ==================================================================

    def assert_summary_shipment_date(self, date_string: str) -> None:
        """Verify the displayed shipment date matches the expected date."""
        expected_display = self._format_summary_date(date_string)
        actual = self.get_summary_shipment_date_text()
        assert expected_display.lower() in actual.lower(), (
            f"Date mismatch: expected '{expected_display}' in '{actual}'"
        )

    def assert_summary_origin_city(self, address: str) -> None:
        city_state = self._extract_city_state(address)
        actual = self.get_summary_origin_city_text()
        assert city_state.lower() in actual.lower(), (
            f"Origin mismatch: expected '{city_state}' in '{actual}'"
        )

    def assert_summary_destination_city(self, address: str) -> None:
        city_state = self._extract_city_state(address)
        actual = self.get_summary_destination_city_text()
        assert city_state.lower() in actual.lower(), (
            f"Destination mismatch: expected '{city_state}' in '{actual}'"
        )

    def assert_summary_item(self, item_label: str) -> None:
        """Verify an item appears in the payment summary."""
        self._expand_shipping_accordion()
        expect(
            self.summary_payment_items.filter(has_text=item_label)
        ).to_be_visible(timeout=10000)

    def assert_summary_matches_challenge(
        self,
        delivery_date: str,
        origin: str,
        destination: str,
        items: list[str] | None = None,
    ) -> None:
        """Full order summary validation against a scenario."""
        self.assert_summary_shipment_date(delivery_date)
        self.assert_summary_origin_city(origin)
        self.assert_summary_destination_city(destination)
        if items:
            for label in items:
                self.assert_summary_item(label)

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def build_summary_item_label(category: str, size: str, index: int = 1) -> str:
        """Build the display label: 'Golf Bags #1 (Standard)'."""
        return f"{category} #{index} ({size})"

    def _expand_shipping_accordion(self) -> None:
        """Click the shipping accordion header to reveal items."""
        try:
            accordion = self.page.get_by_role("button", name="Shipping")
            accordion.wait_for(state="visible", timeout=3000)
            accordion.click()
            expect(self.summary_payment_items.first).to_be_visible(timeout=5000)
        except (PlaywrightTimeout, PlaywrightError):
            pass  # Already expanded or not present

    @staticmethod
    def _extract_city_state(address: str) -> str:
        """
        Extract 'City, ST' from a full address.

        '4321 Main St, Miami Lakes, FL, USA' → 'Miami Lakes, FL'

        Uses Python datetime for robustness instead of manual parsing.
        """
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 3:
            return f"{parts[-3].strip()}, {parts[-2].strip()}"
        # Fallback: return everything after first comma
        return ", ".join(parts[1:]).strip() if len(parts) > 1 else address

    @staticmethod
    def _normalize_date_label(date_string: str) -> str:
        """Extract 'Month DD, YYYY' from input."""
        match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", date_string)
        if not match:
            raise ValueError(f"Cannot parse date: {date_string}")
        month, day, year = match.groups()
        return f"{month} {int(day)}, {year}"

    @staticmethod
    def _format_summary_date(date_string: str) -> str:
        """
        Convert a date string to the summary display format.

        'Wednesday, April 8, 2026' → 'Wed, Apr. 08'

        Uses datetime.strftime() instead of manual month arrays.
        """
        normalized = BookingLoginPage._normalize_date_label(date_string)
        parsed = datetime.strptime(normalized, "%B %d, %Y")

        weekday = parsed.strftime("%a")         # "Wed"
        month = parsed.strftime("%b")           # "Apr"
        day = parsed.strftime("%d")             # "08"

        # Ship Sticks uses "Apr." with a period (except May which has none)
        if month != "May":
            month = f"{month}."

        return f"{weekday}, {month} {day}"
