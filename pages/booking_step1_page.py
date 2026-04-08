"""
BookingStep1Page — shipping options, items, date, and service selection.

This is the most complex page object in the framework.  Key capabilities:
  - Bot-protection detection (PerfDrive / ShieldSquare)
  - Calendar navigation (month-by-month to any target date)
  - Item configuration (add items, select sizes, multi-item support)
  - Shipping method selection (with "Show More" expansion)
  - Weather warning dismissal

Python-specific fixes:
  - Calendar loop raises TimeoutError instead of silently failing
  - Item size selection has a fresh-locator retry for detached elements
  - Regex escaping uses re.escape() instead of manual char replacement
  - Date parsing uses datetime instead of manual month arrays
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from playwright.sync_api import expect, TimeoutError as PlaywrightTimeout

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class BookingStep1Page(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        # -- Trip & address --
        self.trip_type_button = page.get_by_role("button", name=re.compile(r"(?i)round trip|one way"))
        self.one_way_option = page.get_by_role("option", name="One way")
        self.origin_field = page.get_by_role("combobox", name="Where from?")
        self.destination_field = page.get_by_role("combobox", name="Where to?")
        self.first_autocomplete_suggestion = page.get_by_role("option").first

        # -- Warnings --
        self.weather_warning = page.get_by_text("Please note before proceeding")
        self.weather_warning_dismiss_button = page.get_by_role("button", name="I understand")

        # -- Date --
        self.select_date_button = page.get_by_role("button", name="Please select a date")
        self.date_button = page.get_by_role(
            "button",
            name=re.compile(r"(?i)please select a date|[a-z]{3} \d{1,2}, \d{4}"),
        )

        # -- Shipping --
        self.shipping_options_heading = page.get_by_role("heading", name="Shipping Options")
        self.shipment_speeds_heading = page.get_by_role("heading", name="Shipment Speeds")
        self.show_more_options_button = page.get_by_role("button", name=re.compile(r"(?i)show more options"))

        # -- Items --
        self.order_summary = page.get_by_role("heading", name="Order Summary")

        # -- Navigation --
        self.next_button = page.get_by_role("button", name="Next: Traveler Details").first

        # -- Save --
        self.save_button = page.get_by_role("button", name="Save")

        # Service level label mapping (extensible)
        self._service_labels = {
            "Ground": "Ground",
            "Three Day Express": "Three Day Express",
            "Next Day Express": "Next Day Express",
            "Second Day Express": "Second Day Express",
        }

    # ==================================================================
    # Navigation & bot protection
    # ==================================================================

    def goto(self) -> None:
        self.navigate("/book/ship")
        self.accept_cookies_if_present()
        self.assert_loaded()

    def assert_loaded(self) -> None:
        """
        Verify we actually reached the booking page.

        If bot protection (PerfDrive/ShieldSquare) intercepted us,
        raise an explicit error instead of letting tests fail cryptically.
        """
        url = self.page.url
        if "validate.perfdrive.com" in url or "shieldsquare" in url:
            raise RuntimeError(
                f"Navigation was blocked by Ship Sticks bot protection at {url}. "
                "The test runner is reaching a CAPTCHA page instead of the booking flow."
            )
        expect(self.shipping_options_heading).to_be_visible(timeout=15000)
        self.accept_cookies_if_present()

    # ==================================================================
    # Weather warning
    # ==================================================================

    def dismiss_weather_warning_if_present(self, timeout: int = 8000) -> None:
        try:
            self.weather_warning_dismiss_button.wait_for(state="visible", timeout=timeout)
            self.weather_warning_dismiss_button.click()
            self.weather_warning_dismiss_button.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeout:
            pass

    # ==================================================================
    # Address filling (when accessed directly, not from homepage)
    # ==================================================================

    def fill_origin_address(self, address: str) -> None:
        self.type_carefully(self.origin_field, address)
        self.wait_for_autocomplete()
        self.first_autocomplete_suggestion.click()
        expect(self.origin_field).not_to_have_value("")

    def fill_destination_address(self, address: str) -> None:
        self.type_carefully(self.destination_field, address)
        self.wait_for_autocomplete()
        self.first_autocomplete_suggestion.click()
        expect(self.destination_field).not_to_have_value("")

    def save_addresses(self) -> None:
        """Click Save if visible, then dismiss any country note."""
        try:
            self.save_button.wait_for(state="visible", timeout=5000)
            expect(self.save_button).to_be_enabled()
            self.save_button.click()
        except PlaywrightTimeout:
            pass
        self.dismiss_country_note_if_present()

    def select_one_way_shipment(self) -> None:
        self.trip_type_button.click()
        self.one_way_option.click()
        expect(self.trip_type_button).to_contain_text("One way")

    # ==================================================================
    # Date selection
    # ==================================================================

    def select_delivery_date(self, date_string: str) -> None:
        """
        Open the date picker, navigate to the correct month, click the date.

        Args:
            date_string: e.g. "Wednesday, April 8, 2026" or "April 8, 2026"

        Python fix: uses datetime parsing instead of manual month arrays,
        and raises TimeoutError if the target month is not found within
        48 iterations (4 years).
        """
        normalized = self._normalize_date_label(date_string)  # "April 8, 2026"
        parsed = datetime.strptime(normalized, "%B %d, %Y")
        target_month = parsed.strftime("%B")   # "April"
        target_year = str(parsed.year)          # "2026"

        # Open the calendar
        expect(self.select_date_button).to_be_enabled(timeout=5000)
        self.select_date_button.click()

        # Navigate month-by-month until we reach the target
        calendar_panel = self.page.locator('[role="grid"]').locator("..").first
        next_month_btn = calendar_panel.get_by_role("button").nth(1)

        max_clicks = 48  # 4 years of months — should be more than enough
        for _ in range(max_clicks):
            month_label = calendar_panel.locator(
                r"text=/[A-Za-z]+ \d{4}/"
            ).first.text_content()
            if month_label and target_month in month_label and target_year in month_label:
                break
            next_month_btn.click()
        else:
            raise TimeoutError(
                f"Could not navigate calendar to {target_month} {target_year} "
                f"within {max_clicks} clicks"
            )

        # Click the specific date cell
        self.page.get_by_role("gridcell", name=normalized).click()

        # Verify the date button updated
        short_month = parsed.strftime("%b")  # "Apr"
        day_number = str(parsed.day)
        expect(self.date_button).to_have_text(
            re.compile(rf"(?i){short_month}\s+{day_number},\s+{target_year}")
        )
        expect(self.shipment_speeds_heading).to_be_visible()

    # ==================================================================
    # Shipping method
    # ==================================================================

    def select_shipping_method(self, service_level: str) -> None:
        """Select a shipping speed radio button."""
        expect(self.shipment_speeds_heading).to_be_visible(timeout=10000)
        label = self._resolve_service_level(service_level)

        # Make sure at least Ground is visible
        expect(self.page.get_by_text(re.compile(r"(?i)ground")).first).to_be_visible(timeout=15000)

        # Some options are hidden behind "Show More"
        if re.match(r"(?i)second day express", label):
            self._show_more_shipping_options()
            expect(
                self.page.get_by_text(re.compile(re.escape(label), re.IGNORECASE)).first
            ).to_be_visible(timeout=10000)

        radio = self.page.get_by_role(
            "radio", name=re.compile(re.escape(label), re.IGNORECASE)
        ).first
        expect(radio).to_be_visible(timeout=10000)
        radio.click()
        expect(radio).to_be_checked()

    def _show_more_shipping_options(self) -> None:
        try:
            self.show_more_options_button.wait_for(state="visible", timeout=5000)
            self.show_more_options_button.click()
        except PlaywrightTimeout:
            pass  # Already expanded

    # ==================================================================
    # Item configuration
    # ==================================================================

    def add_item(self, category: str, quantity: int = 1) -> None:
        """Click the 'Increase {category} count' button *quantity* times."""
        increase_btn = self.page.get_by_role(
            "button",
            name=re.compile(rf"(?i)increase {re.escape(category)} count"),
        )
        self.page.get_by_role("heading", name="Item Details").scroll_into_view_if_needed()

        for _ in range(quantity):
            expect(increase_btn).to_be_enabled()
            increase_btn.click()

        expect(self.order_summary).to_be_visible()

    def select_item_size(
        self,
        category: str,
        size_label: str,
        item_index: int = 1,
    ) -> None:
        """
        Select a size for a specific item (e.g. "Golf Bags #1" → "Standard").

        Uses a retry strategy for detached elements: if the first attempt
        fails because the DOM re-rendered, we re-query with a fresh locator.
        """
        item_label = f"{category} #{item_index}"

        # Brief wait for DOM stability after adding items
        self.page.wait_for_timeout(500)

        item_section = (
            self.page.get_by_text(item_label, exact=True).locator("..").first
        )
        expect(item_section).to_be_visible(timeout=10000)

        size_btn = item_section.get_by_role(
            "button", name=re.compile(re.escape(size_label), re.IGNORECASE)
        )
        expect(size_btn).to_be_visible(timeout=10000)

        try:
            size_btn.scroll_into_view_if_needed()
            size_btn.click()
        except Exception:
            # Element may have detached during scroll — re-query
            fresh_section = (
                self.page.get_by_text(item_label, exact=True).locator("..").first
            )
            fresh_btn = fresh_section.get_by_role(
                "button", name=re.compile(re.escape(size_label), re.IGNORECASE)
            )
            expect(fresh_btn).to_be_visible(timeout=5000)
            fresh_btn.scroll_into_view_if_needed()
            fresh_btn.click()

    def configure_items(self, item_configs: list[dict]) -> None:
        """
        Add and size all items described by *item_configs*.

        Each dict must have: category, quantity, sizes (list).
        """
        normalized = self._normalize_item_configs(item_configs)
        for item in normalized:
            self.add_item(item["category"], item["quantity"])
            for idx, size in enumerate(item["sizes"]):
                self.select_item_size(item["category"], size, idx + 1)

    # ==================================================================
    # Navigation
    # ==================================================================

    def proceed_to_next_step(self) -> None:
        expect(self.next_button).to_be_enabled(timeout=10000)
        self.next_button.click()

    def get_origin_value(self) -> str:
        return self.origin_field.input_value()

    def get_destination_value(self) -> str:
        return self.destination_field.input_value()

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _normalize_date_label(date_string: str) -> str:
        """
        Extract 'Month DD, YYYY' from various input formats.

        'Wednesday, April 8, 2026' → 'April 8, 2026'
        'April 8, 2026'            → 'April 8, 2026'
        """
        match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", date_string)
        if not match:
            raise ValueError(f"Cannot parse date: {date_string}")
        month, day, year = match.groups()
        return f"{month} {int(day)}, {year}"

    def _resolve_service_level(self, level: str) -> str:
        """Map user-friendly service level name to the UI label."""
        return self._service_labels.get(level, level)

    @staticmethod
    def _normalize_item_configs(configs: list[dict]) -> list[dict]:
        """
        Normalize item config dicts to a consistent shape:
          { category: str, quantity: int, sizes: list[str] }
        """
        result = []
        for item in configs:
            sizes = item.get("sizes", [])
            if not sizes and "size" in item:
                sizes = [item["size"]] * (item.get("quantity", 1))
            quantity = item.get("quantity", len(sizes) or 1)

            if len(sizes) != quantity:
                raise ValueError(
                    f"Item config mismatch for {item.get('category', '?')}: "
                    f"quantity={quantity}, sizes={len(sizes)}"
                )
            result.append({
                "category": item["category"],
                "quantity": quantity,
                "sizes": sizes,
            })
        return result

    @staticmethod
    def get_challenge_items(scenario: dict) -> list[dict]:
        """
        Extract normalized item configs from a scenario dict.

        Supports both formats:
          - scenario["items"] = [{ category, quantity, sizes }]
          - scenario["item_category"] + scenario["item_size"] (legacy)
        """
        if "items" in scenario and scenario["items"]:
            return BookingStep1Page._normalize_item_configs(scenario["items"])
        return BookingStep1Page._normalize_item_configs([{
            "category": scenario["item_category"],
            "quantity": 1,
            "sizes": [scenario["item_size"]],
        }])
