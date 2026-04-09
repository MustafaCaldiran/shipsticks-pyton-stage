"""
HomePage — landing page, quote widget, and authentication modals.

Covers:
  - Quote initiation (origin, destination, trip type)
  - Sign In modal
  - Sign Up flow (form → password → phone verification)
  - Post-login assertion
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class HomePage(BasePage):

    def __init__(self, page: "Page", base_url: str = ""):
        super().__init__(page, base_url)

        # -- Quote widget --
        self.origin_field = page.get_by_role("combobox", name="Where from?")
        self.destination_field = page.get_by_role("combobox", name="Where to?")
        self.trip_type_button = page.get_by_role("button", name=re.compile(r"round trip|one way", re.I))
        self.one_way_option = page.get_by_role("option", name="One way")
        self.get_started_button = page.get_by_role("button", name="Get started").first
        self.hero_heading = page.get_by_role("heading", name=re.compile(r"skip baggage claim", re.I))
        self.first_autocomplete_suggestion = page.get_by_role("option").first

        # -- Sign In modal --
        self.sign_in_button = page.get_by_text("Sign In")
        self.sign_in_menu_item = page.get_by_role("menuitem", name="Sign In")
        self.login_modal_heading = page.get_by_role("button", name="Log In")
        self.shipsticks_logo_in_modal = page.get_by_role(
            "img", name=re.compile(r"shipstickstextonlydark", re.I)
        )
        self.email_field_in_modal = page.get_by_placeholder("Email address")
        self.password_field_in_modal = page.get_by_role("textbox", name="Password*")
        self.login_button_in_modal = page.get_by_role("button", name="Log In")
        self.sign_up_link = page.get_by_role("link", name="Sign up here.")
        self.user_account = page.get_by_role("button", name="Account options menu")
        self.online_bill_pay = page.get_by_role("menuitem", name="Online Bill Pay")

        # -- Sign Up modal --
        self.sign_up_heading = page.locator("h2").filter(has_text="Sign Up").first
        self.first_name_field = page.get_by_role("textbox", name="First name*")
        self.last_name_field = page.get_by_role("textbox", name="Last name*")
        self.email_field_in_signup = page.locator('input[name="email"][type="text"]').last
        self.country_dropdown = (
            page.locator('[role="dialog"]')
            .get_by_role("combobox")
            .filter(has_text=re.compile(r"United States|Select"))
            .or_(page.locator('[role="dialog"]').get_by_role("combobox").nth(0))
        )
        self.how_did_you_hear_dropdown = (
            page.locator('[role="dialog"]')
            .locator('button[aria-haspopup="listbox"]')
            .first
        )
        self.phone_number_field = page.get_by_placeholder("555-555-5555")
        self.continue_button = page.get_by_role("button", name="Continue to Create Password")

        # -- Password creation --
        self.finishing_signup_heading = page.get_by_role(
            "heading", name=re.compile(r"create.*password|finish.*sign.*up|set.*password|choose.*password|almost done", re.I)
        )
        self.signup_password_field = page.locator("#password")
        self.confirm_password_field = page.get_by_role("textbox", name="Confirm Password*")
        self.terms_checkbox = page.get_by_role(
            "checkbox", name=re.compile(r"by creating an account", re.I)
        )
        self.finish_signup_button = page.get_by_role(
            "button", name=re.compile(r"finish sign up and verify number", re.I)
        )

        # -- Phone verification --
        self.verify_number_heading = page.get_by_role(
            "heading", name=re.compile(r"verify your phone number", re.I)
        )
        self.skip_for_now_button = page.get_by_role(
            "button", name=re.compile(r"skip for now", re.I)
        )
        self.verify_number_confirm_button = page.get_by_role("button", name="Confirm")

    # ==================================================================
    # Navigation
    # ==================================================================

    def goto(self) -> None:
        """Navigate to the homepage with full widget-blocking setup."""
        self.block_chat_widgets()
        self.navigate("/")
        self.accept_cookies_if_present()
        expect(self.hero_heading).to_be_visible(timeout=15000)
        expect(self.get_started_button).to_be_disabled()

    # ==================================================================
    # Quote widget
    # ==================================================================

    def select_one_way_shipment(self) -> None:
        self.trip_type_button.click()
        self.one_way_option.click()
        expect(self.trip_type_button).to_have_text(re.compile(r"one way", re.I))

    def fill_origin_address(self, address: str) -> None:
        self.type_carefully(self.origin_field, address)
        self.wait_for_autocomplete()
        self.first_autocomplete_suggestion.click()

    def fill_destination_address(self, address: str) -> None:
        self.type_carefully(self.destination_field, address)
        self.wait_for_autocomplete()
        self.first_autocomplete_suggestion.click()

    def start_quote(
        self,
        shipment_type: str = "One-way",
        origin: str = "",
        destination: str = "",
    ) -> None:
        """Complete the quote widget and click Get Started."""
        if "one" in shipment_type.lower():
            self.select_one_way_shipment()
        self.fill_origin_address(origin)
        self.fill_destination_address(destination)
        expect(self.get_started_button).to_be_enabled(timeout=10000)
        self.get_started_button.click()

    # ==================================================================
    # Sign In
    # ==================================================================

    def click_sign_in(self) -> None:
        expect(self.sign_in_button).to_be_visible(timeout=10000)
        self.sign_in_button.click()
        expect(self.sign_in_menu_item).to_be_visible(timeout=10000)
        self.sign_in_menu_item.click()

    def assert_sign_in_modal_visible(self) -> None:
        expect(self.login_modal_heading).to_be_visible(timeout=10000)
        expect(self.shipsticks_logo_in_modal).to_be_visible(timeout=10000)

    # ==================================================================
    # Sign Up
    # ==================================================================

    def switch_to_sign_up(self) -> None:
        self.sign_up_link.click()

    def assert_sign_up_modal_visible(self) -> None:
        expect(self.sign_up_heading).to_be_visible(timeout=10000)

    def select_country(self, country: str) -> None:
        """Open the country dropdown, search, and select an exact match."""
        self.country_dropdown.click(click_count=3)
        self.country_dropdown.press_sequentially(country, delay=50)
        self.page.get_by_role("option", name=country, exact=True).click()
        expect(self.country_dropdown).to_have_value(country, timeout=10000)

    def select_how_did_you_hear(self, option_text: str) -> None:
        self.how_did_you_hear_dropdown.click()
        self.page.wait_for_timeout(500)
        self.page.get_by_role("option", name=option_text, exact=True).click()

    def fill_sign_up_form(self, data: dict) -> None:
        """
        Fill the sign-up form with the provided data dict.

        Expected keys: first_name, last_name, email, country,
                       how_did_you_hear, phone_number
        """
        first_name = data.get("first_name") or data.get("firstName")
        last_name = data.get("last_name") or data.get("lastName")
        email = data["email"]
        country = data.get("country")
        how_did_you_hear = data.get("how_did_you_hear") or data.get("howDidYouHear")
        phone_number = data.get("phone_number") or data.get("phoneNumber")

        self.type_with_focus_guard(self.first_name_field, first_name)
        self.type_with_focus_guard(self.last_name_field, last_name)
        self.type_with_focus_guard(self.email_field_in_signup, email)

        if country:
            self.select_country(country)
        if how_did_you_hear:
            self.select_how_did_you_hear(how_did_you_hear)
        if phone_number:
            self.type_with_focus_guard(self.phone_number_field, phone_number)

    def click_continue_to_create_password(self) -> None:
        expect(self.continue_button).to_be_enabled(timeout=10000)
        self.continue_button.click()

    # ==================================================================
    # Password creation
    # ==================================================================

    def assert_finishing_signup_visible(self) -> None:
        expect(self.finishing_signup_heading).to_be_visible(timeout=10000)

    def fill_password_fields(self, password: str) -> None:
        """Fill both password fields, check terms, and submit."""
        self.assert_finishing_signup_visible()

        # Use focus guard because Intercom loves to steal focus here
        self.type_with_focus_guard(self.signup_password_field, password)
        self.type_with_focus_guard(self.confirm_password_field, password)

        # Terms checkbox
        expect(self.terms_checkbox).to_be_visible(timeout=10000)
        expect(self.terms_checkbox).to_be_enabled(timeout=10000)
        self.terms_checkbox.click()
        expect(self.terms_checkbox).to_be_checked()

        expect(self.finish_signup_button).to_be_enabled(timeout=5000)
        self.finish_signup_button.click()

    # ==================================================================
    # Phone verification
    # ==================================================================

    def verify_your_number(self) -> None:
        """Handle the phone-verification screen by clicking Skip."""
        expect(self.verify_number_heading).to_be_visible(timeout=15000)
        expect(self.skip_for_now_button).to_be_visible(timeout=10000)
        self.skip_for_now_button.click()

    def skip_verify_your_number(self) -> None:
        """JavaScript-compatible alias for the phone-verification skip step."""
        self.verify_your_number()

    # ==================================================================
    # Post-auth assertions
    # ==================================================================

    def assert_logged_in(self, user_name: str) -> None:
        """Verify the header shows the logged-in user greeting."""
        greeting = self.page.get_by_text(f"Hi, {user_name}")
        expect(greeting).to_be_visible(timeout=15000)
