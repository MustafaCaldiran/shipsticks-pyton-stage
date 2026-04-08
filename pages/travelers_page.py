"""
TravelersPage — traveler details and address verification.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class TravelersPage(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        self.heading = page.get_by_role("heading", name="Traveler Details")
        self.address_field = page.get_by_role("combobox", name="Address*").first
        self.city_field = page.get_by_role("textbox", name=re.compile(r"(?i)city\*"))
        self.state_field = page.get_by_role("combobox", name=re.compile(r"(?i)choose state"))
        self.zip_field = page.get_by_role("textbox", name=re.compile(r"(?i)zip code\*"))
        self.next_button = (
            page.locator("span").filter(has_text="Next: Package and Protection").first
        )

    def assert_loaded(self) -> None:
        assert "/book/travelers" in self.page.url, f"Expected /book/travelers, got {self.page.url}"
        expect(self.heading).to_be_visible(timeout=15000)

    def assert_traveler_name(self, first_name: str, last_name: str) -> None:
        """
        Verify the traveler name is displayed (case-insensitive).

        Uses XPath translate() for case-insensitive text matching.
        Names are lowercased on both sides to avoid XPath injection.
        """
        full_name = f"{first_name} {last_name}".lower()
        # Escape quotes in name to prevent XPath injection
        safe_name = full_name.replace("'", "\\'")
        xpath = (
            f"(//div[contains("
            f"translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
            f"'{safe_name}')])[1]"
        )
        locator = self.page.locator(xpath)
        expect(locator).to_be_visible(timeout=10000)

    def assert_address_fields(
        self,
        street_address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
    ) -> None:
        """Assert pre-filled address fields (all parameters optional)."""
        if street_address:
            expect(self.address_field).to_have_value(
                re.compile(re.escape(street_address), re.IGNORECASE)
            )
        if city:
            expect(self.city_field).to_have_value(
                re.compile(re.escape(city), re.IGNORECASE)
            )
        if state:
            expect(self.state_field).to_have_value(
                re.compile(re.escape(state), re.IGNORECASE)
            )
        if zip_code:
            expect(self.zip_field).to_have_value(
                re.compile(re.escape(zip_code), re.IGNORECASE)
            )

    def proceed_to_package_and_protection(self) -> None:
        expect(self.next_button).to_be_visible(timeout=10000)
        self.next_button.click()
