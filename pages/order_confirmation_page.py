"""
OrderConfirmationPage — success screen after payment.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class OrderConfirmationPage(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        self.heading = page.get_by_role(
            "heading", name=re.compile(r"(?i)your order is complete")
        )

    def assert_loaded(self) -> None:
        assert "/order-confirmation" in self.page.url, (
            f"Expected /order-confirmation, got {self.page.url}"
        )
        expect(self.heading).to_be_visible(timeout=30000)
