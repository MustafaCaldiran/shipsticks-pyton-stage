"""
PaymentPage — coverage selection, pickup method, and credit card entry.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect, TimeoutError as PlaywrightTimeout

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class PaymentPage(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        self.heading = page.get_by_role(
            "heading", name=re.compile(r"(?i)additional options.*payment details")
        )
        self.coverage_dropdown = page.get_by_role("button", name=re.compile(r"(?i)coverage amount\*"))

        # Pickup method
        self.have_them_picked_up = page.get_by_text("Have them picked up")
        self.drop_them_off = page.get_by_text("Bring your bags to a FedEx location.")
        self.pickup_fee_value = page.locator(
            "//span[normalize-space()='Pickup Fee']/following-sibling::span"
        )

        # Credit card fields
        self.card_number = page.get_by_role("textbox", name=re.compile(r"(?i)card number\*"))
        self.expiration_date = page.get_by_role("textbox", name=re.compile(r"(?i)expiration date\*"))
        self.cvc = page.get_by_role("textbox", name=re.compile(r"(?i)cvc\*"))
        self.billing_country_button = page.get_by_role("button", name="United States of America")
        self.billing_zip = page.get_by_role("textbox", name=re.compile(r"(?i)billing zip code\*"))
        self.card_first_name = page.get_by_role("textbox", name=re.compile(r"(?i)first name\*"))
        self.card_last_name = page.get_by_role("textbox", name=re.compile(r"(?i)last name\*"))

        # Navigation
        self.next_review_order_button = (
            page.locator("span").filter(has_text="Next: Review Order").first
        )

    def assert_loaded(self) -> None:
        assert "/book/pay" in self.page.url, f"Expected /book/pay, got {self.page.url}"
        expect(self.heading).to_be_visible(timeout=30000)

    def select_coverage_amount(self, coverage_text: str) -> None:
        """Open dropdown and select the matching coverage option."""
        self.coverage_dropdown.click()
        self.page.get_by_text(coverage_text, exact=True).click()

    def select_pickup_method(self, method: str) -> None:
        """Select pickup or drop-off."""
        if method == "haveThemPickedUp":
            self.have_them_picked_up.click()
        else:
            self.drop_them_off.click()

    def assert_pickup_fee(self, method: str) -> None:
        """Verify the pickup fee is displayed correctly."""
        if method == "haveThemPickedUp":
            fee_from_label = self.page.locator(
                "//span[normalize-space()='Have them picked up']/following::span[contains(text(),'$')][1]"
            ).text_content()
            expect(self.pickup_fee_value).to_have_text((fee_from_label or "").strip())
        else:
            expect(self.pickup_fee_value).to_have_text("$0.00")

    def fill_credit_card(self, data: dict) -> None:
        """
        Fill all credit card fields.

        Expected keys: first_name, last_name, card_number,
                       expiration_date, cvc, billing_country (optional),
                       zip_code (optional)
        """
        self.card_first_name.fill(data["first_name"])
        self.card_last_name.fill(data["last_name"])
        self.card_number.fill(data["card_number"])
        self.expiration_date.fill(data["expiration_date"])
        self.cvc.fill(data["cvc"])

        if data.get("billing_country"):
            self.billing_country_button.click()
            self.page.get_by_text(data["billing_country"], exact=True).click()

        if data.get("zip_code"):
            try:
                self.billing_zip.wait_for(state="visible", timeout=5000)
                self.billing_zip.fill(data["zip_code"])
            except PlaywrightTimeout:
                pass

    def proceed_to_review_order(self) -> None:
        expect(self.next_review_order_button).to_be_visible(timeout=10000)
        self.next_review_order_button.click()
