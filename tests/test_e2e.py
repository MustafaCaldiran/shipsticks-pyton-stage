"""
Full end-to-end test: Sign Up → Quote → Step 1 → Travelers → Payment → Review → Confirmation.

This is the most comprehensive test in the suite — it exercises every page object
and verifies the complete user journey from anonymous visitor to paid order.
"""

import pytest

from data.test_data import SCENARIOS, AUTH_DATA, get_sign_up_data
from pages.home_page import HomePage
from pages.booking_step1_page import BookingStep1Page
from pages.booking_login_page import BookingLoginPage
from pages.travelers_page import TravelersPage
from pages.payment_page import PaymentPage
from pages.review_page import ReviewPage
from pages.order_confirmation_page import OrderConfirmationPage


@pytest.mark.e2e
class TestEndToEnd:

    def test_sign_up_then_complete_booking(self, page, base_url):
        """
        Complete user journey from sign-up through order confirmation.

        Uses the 'challenge' scenario (the primary happy path).
        """
        scenario = SCENARIOS["challenge"]
        sign_up_data = get_sign_up_data()
        payment_data = AUTH_DATA["payment"]

        # Instantiate all page objects
        home = HomePage(page, base_url)
        booking = BookingStep1Page(page, base_url)
        login_page = BookingLoginPage(page)
        travelers = TravelersPage(page)
        payment = PaymentPage(page)
        review = ReviewPage(page)
        confirmation = OrderConfirmationPage(page)

        # -- 1. Sign Up --
        home.goto()
        home.click_sign_in()
        home.switch_to_sign_up()
        home.fill_sign_up_form(sign_up_data)
        home.click_continue_to_create_password()
        home.fill_password_fields(sign_up_data["password"])
        home.verify_your_number()
        home.assert_logged_in(sign_up_data["first_name"])

        # -- 2. Quote --
        home.start_quote(
            shipment_type=scenario["shipment_type"],
            origin=scenario["origin"],
            destination=scenario["destination"],
        )

        # -- 3. Step 1: Shipping Options --
        booking.assert_loaded()
        booking.dismiss_weather_warning_if_present()

        challenge_items = BookingStep1Page.get_challenge_items(scenario)
        booking.configure_items(challenge_items)
        booking.select_delivery_date(scenario["delivery_date"])
        booking.select_shipping_method(scenario["service_level"])
        booking.proceed_to_next_step()

        # -- 4. Travelers --
        travelers.assert_loaded()
        travelers.assert_traveler_name(sign_up_data["first_name"], sign_up_data["last_name"])
        travelers.proceed_to_package_and_protection()

        # -- 5. Payment --
        payment.assert_loaded()
        if "coverage_amount" in scenario:
            payment.select_coverage_amount(scenario["coverage_amount"])
        if "pickup_method" in scenario:
            payment.select_pickup_method(scenario["pickup_method"])
            payment.assert_pickup_fee(scenario["pickup_method"])
        payment.fill_credit_card(payment_data)
        payment.proceed_to_review_order()

        # -- 6. Review --
        review.assert_loaded()
        review.assert_billing_country(payment_data["billing_country"])
        if "coverage_amount" in scenario:
            review.assert_coverage_text(scenario["coverage_amount"])
        review.confirm_and_pay()

        # -- 7. Confirmation --
        confirmation.assert_loaded()
