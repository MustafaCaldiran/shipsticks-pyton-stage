from __future__ import annotations

import pytest

from data.test_data import AUTH_DATA, SCENARIOS
from pages.booking_step1_page import BookingStep1Page
from pages.order_confirmation_page import OrderConfirmationPage
from pages.payment_page import PaymentPage
from pages.review_page import ReviewPage
from pages.travelers_page import TravelersPage
from utils.create_user import create_user_via_ui


@pytest.mark.e2e
class TestEndToEnd:
    def test_sign_up_then_complete_booking_step_1(self, page, base_url):
        scenario = SCENARIOS["challenge"]

        booking_page = BookingStep1Page(page, base_url)
        travelers_page = TravelersPage(page)
        payment_page = PaymentPage(page)
        review_page = ReviewPage(page)
        order_confirmation_page = OrderConfirmationPage(page)

        created = create_user_via_ui(page, base_url)
        home_page = created["homePage"]

        home_page.start_quote(
            shipment_type=scenario["shipmentType"],
            origin=scenario["origin"],
            destination=scenario["destination"],
        )

        booking_page.assert_loaded()
        booking_page.dismiss_weather_warning_if_present()

        challenge_items = booking_page.get_challenge_items(scenario)
        booking_page.configure_items(challenge_items)
        booking_page.select_delivery_date(scenario["deliveryDate"])
        booking_page.select_shipping_method(scenario["serviceLevel"])
        booking_page.proceed_to_next_step()

        travelers_page.assert_loaded()
        travelers_page.assert_traveler_name(created["firstName"], created["lastName"])
        travelers_page.assert_address_fields(
            street_address=scenario["origin"].split(",")[0].split(" ")[:2][0] + " " + scenario["origin"].split(",")[0].split(" ")[:2][1]
        )
        travelers_page.proceed_to_package_and_protection()

        payment_page.assert_loaded()
        payment_page.select_coverage_amount(scenario["coverageAmount"])
        payment_page.select_pickup_method(scenario["pickupMethod"])
        payment_page.assert_pickup_fee(scenario["pickupMethod"])
        payment_page.fill_credit_card(AUTH_DATA["payment"])
        payment_page.proceed_to_review_order()

        review_page.assert_loaded()
        review_page.assert_billing_country(AUTH_DATA["payment"]["billingCountry"])
        review_page.assert_coverage_text(scenario["coverageAmount"])
        review_page.confirm_and_pay()

        order_confirmation_page.assert_loaded()
