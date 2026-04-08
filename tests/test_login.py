from __future__ import annotations

import pytest

from data.test_data import get_sign_up_data
from pages.home_page import HomePage


@pytest.mark.smoke
class TestLogin:
    def test_opens_login_modal_when_sign_in_is_clicked(self, page, base_url):
        home_page = HomePage(page, base_url)
        sign_up = get_sign_up_data()

        home_page.goto()
        home_page.click_sign_in()
        home_page.assert_sign_in_modal_visible()

        home_page.switch_to_sign_up()
        home_page.assert_sign_up_modal_visible()

        home_page.fill_sign_up_form(sign_up)
        home_page.click_continue_to_create_password()
        home_page.fill_password_fields(sign_up["password"])
        home_page.skip_verify_your_number()
        home_page.assert_logged_in(sign_up["firstName"])
