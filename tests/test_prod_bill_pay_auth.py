from __future__ import annotations

import pytest
from playwright.sync_api import expect

from config.settings import settings
from pages.home_page import HomePage
from utils.network_logger import attach_network_logging, dump_cookies, with_network_logging


@pytest.mark.skipif(settings.base_url != "https://www.shipsticks.com", reason="Production-only diagnostic parity test.")
class TestProdBillPayAuth:
    def test_prod_bill_pay_auth_phone_verification_gate_and_logout_sync(self, page, context):
        home = HomePage(page, "https://www.shipsticks.com")

        with with_network_logging(page, "MAIN"):
            home.goto()
            home.click_sign_in()
            home.assert_sign_in_modal_visible()

            modal = page.get_by_role("dialog")
            home.type_with_focus_guard(modal.get_by_role("textbox", name="Email address"), settings.prod_email)
            home.type_with_focus_guard(modal.locator('input[type="password"]'), settings.prod_password)
            modal.get_by_role("button", name="Log In").click()
            expect(page.get_by_role("button", name="Account options menu")).to_be_visible(timeout=25000)

        dump_cookies(context, "AFTER MAIN-SITE LOGIN")

        bill_pay_item = home.online_bill_pay
        for attempt in range(1, 4):
            home.dismiss_chat_widget_if_present()
            page.wait_for_timeout(500)
            home.user_account.click()
            try:
                expect(bill_pay_item).to_be_visible(timeout=4000)
                break
            except Exception:
                if attempt == 3:
                    raise

        context.once("page", lambda new_tab: attach_network_logging(new_tab, "VISIT-1"))
        tab1 = None
        with context.expect_page() as new_page_info:
            bill_pay_item.click()
        tab1 = new_page_info.value

        tab1.wait_for_load_state("domcontentloaded")
        tab1.wait_for_timeout(3000)
        logged_in_visit1 = tab1.get_by_role("link", name=r"Hello,.*My Account").is_visible()
        dump_cookies(context, "AFTER VISIT 1 LOADED")

        if logged_in_visit1:
            logout_link = tab1.get_by_role("link", name="Logout").first
            expect(logout_link).to_be_visible(timeout=10000)
            with with_network_logging(tab1, "LOGOUT"):
                logout_link.click()
                tab1.wait_for_load_state("domcontentloaded")
                tab1.wait_for_timeout(2000)

            dump_cookies(context, "AFTER BILL-PAY LOGOUT")
            page.bring_to_front()

            with with_network_logging(page, "MAIN-RELOAD"):
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

            dump_cookies(context, "MAIN SITE AFTER BILL-PAY LOGOUT")
