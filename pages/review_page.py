"""
ReviewPage — final order review before payment confirmation.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class ReviewPage(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        self.heading = page.get_by_role(
            "heading", name="Additional Options & Payment Details"
        )

    def assert_loaded(self) -> None:
        assert "/book/review" in self.page.url, f"Expected /book/review, got {self.page.url}"
        expect(self.heading).to_be_visible(timeout=30000)

    def assert_billing_country(self, country: str) -> None:
        expect(self.page.get_by_text(country).first).to_be_visible(timeout=10000)

    def assert_coverage_text(self, coverage_amount: str) -> None:
        """
        Verify the coverage summary displays the correct amount.

        Input: '$2,500.00 ($8.99)' → asserts 'Covers up to $2,500'
        """
        # Extract the dollar amount (e.g. "$2,500.00")
        match = re.search(r"\$([\d,]+(?:\.\d{2})?)", coverage_amount)
        if match:
            amount = match.group(0).split(".")[0]  # "$2,500"
            expect(
                self.page.get_by_text(re.compile(rf"covers up to.*{re.escape(amount)}", re.I)).first
            ).to_be_visible(timeout=10000)

    def confirm_and_pay(self) -> None:
        btn = self.page.get_by_role("button", name=re.compile(r"confirm and pay", re.I))
        expect(btn).to_be_enabled(timeout=10000)
        btn.click()
