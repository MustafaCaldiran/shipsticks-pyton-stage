"""
Login / Sign-Up flow tests.

Tests the complete sign-up journey:
  Sign In modal → Sign Up form → Password creation → Phone verification → Logged in
"""

import pytest

from data.test_data import get_sign_up_data
from pages.home_page import HomePage


@pytest.mark.smoke
class TestLogin:

    def test_opens_login_modal_and_completes_sign_up(self, page, base_url):
        """
        Complete sign-up flow using a dynamically generated email.

        Steps:
          1. Open Sign In modal from homepage
          2. Switch to Sign Up
          3. Fill registration form (unique email each run)
          4. Create password
          5. Skip phone verification
          6. Assert logged-in greeting
        """
        home = HomePage(page, base_url)
        sign_up_data = get_sign_up_data()

        home.goto()
        home.click_sign_in()
        home.assert_sign_in_modal_visible()

        home.switch_to_sign_up()
        home.assert_sign_up_modal_visible()

        home.fill_sign_up_form(sign_up_data)
        home.click_continue_to_create_password()

        home.fill_password_fields(sign_up_data["password"])

        home.verify_your_number()
        home.assert_logged_in(sign_up_data["first_name"])
