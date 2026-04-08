from __future__ import annotations

import json

import pytest
from playwright.sync_api import expect

from data.test_data import SCENARIOS
from pages.booking_step1_page import BookingStep1Page
from pages.home_page import HomePage

MOCK_RATE_GROUND = {
    "carrierServiceLevel": {
        "serviceLevel": {"bestValue": False, "displayName": "Ground", "systemName": "DOMESTIC_GROUND", "id": "5b314854c7170f610b00000f"},
        "carrier": {"systemName": "FEDEX_GROUND"},
    },
    "itemRates": [{
        "priceCents": 7499, "adjustedPriceCents": 0,
        "product": {"id": "5c5e2d376928b97125000007", "productLine": {"id": "5c5e2d376928b97125000001", "displayName": "Golf Bags"}},
        "quantity": 1,
        "serviceRate": {"id": "635a895b7ef97126189eb359", "carrierServiceLevel": {"id": "5b314854c7170f610b000045"}},
        "totalPriceCents": 7499, "totalAdjustedPriceCents": 0, "isPreferred": False,
    }],
    "shipDate": "2026-04-07", "transitTime": 6, "isOffline": False,
}

MOCK_RATE_NEXT_DAY_EXPRESS = {
    "carrierServiceLevel": {
        "serviceLevel": {"bestValue": True, "displayName": "Next Day Express", "systemName": "DOMESTIC_1_DAY", "id": "5b314854c7170f610b000006"},
        "carrier": {"systemName": "FEDEX_EXPRESS"},
    },
    "itemRates": [{
        "priceCents": 16499, "adjustedPriceCents": 0,
        "product": {"id": "5c5e2d376928b97125000007", "productLine": {"id": "5c5e2d376928b97125000001", "displayName": "Golf Bags"}},
        "quantity": 1,
        "serviceRate": {"id": "61e169335bce0d016756b8b4", "carrierServiceLevel": {"id": "5b314854c7170f610b00003e"}},
        "totalPriceCents": 16499, "totalAdjustedPriceCents": 0, "isPreferred": False,
    }],
    "shipDate": "2026-04-14", "transitTime": 1, "isOffline": False,
}


def _go_to_booking_step1(page, base_url):
    home = HomePage(page, base_url)
    booking = BookingStep1Page(page, base_url)
    scenario = SCENARIOS["challenge"]

    home.goto()
    home.start_quote(
        shipment_type=scenario["shipmentType"],
        origin=scenario["origin"],
        destination=scenario["destination"],
    )
    booking.assert_loaded()
    booking.dismiss_weather_warning_if_present()
    return booking, scenario


@pytest.mark.network
class TestApiInterception:
    def test_booking_form_sends_correct_origin_destination_and_item_count(self, page, base_url):
        captured_payload = {"value": None}

        def handler(route):
            post_data = route.request.post_data
            if post_data:
                body = json.loads(post_data)
                if body.get("operationName") == "GetDeliverByTransitRates":
                    captured_payload["value"] = body["variables"]["input"]
            route.continue_()

        page.route("**/graphql", handler)
        booking, scenario = _go_to_booking_step1(page, base_url)
        booking.configure_items(booking.get_challenge_items(scenario))
        booking.select_delivery_date(scenario["deliveryDate"])

        expect.poll(lambda: captured_payload["value"], message="GetDeliverByTransitRates was never called", timeout=15000).not_to_be_none()
        payload = captured_payload["value"]
        assert payload["shipRoute"]["origin"]["city"] == "Los Angeles"
        assert payload["shipRoute"]["origin"]["state"] == "CA"
        assert payload["shipRoute"]["destination"]["city"] == "Miami Lakes"
        assert payload["shipRoute"]["destination"]["state"] == "FL"
        assert len(payload["products"]) == 1
        assert payload["products"][0]["quantity"] == 1
        assert payload["direction"] == "outbound"
        page.unroute("**/graphql", handler)

    def test_booking_page_does_not_crash_or_go_blank_when_network_goes_offline(self, page, context, base_url):
        page.goto(f"{base_url}/book/ship", wait_until="domcontentloaded")
        try:
            button = page.get_by_role("button", name="Accept all cookies")
            button.wait_for(state="visible", timeout=4000)
            button.click()
        except Exception:
            pass

        context.set_offline(True)
        expect(page.get_by_role("heading", name="Shipping Options")).to_be_visible()
        expect(page.get_by_role("combobox", name="Where from?")).to_be_visible()
        context.set_offline(False)

    def test_shows_fallback_ui_when_no_shipping_rates_are_returned(self, page, base_url):
        def handler(route):
            post_data = route.request.post_data
            if post_data:
                body = json.loads(post_data)
                if body.get("operationName") == "GetDeliverByTransitRates":
                    route.fulfill(status=200, headers={"Content-Type": "application/json"}, body=json.dumps({"data": {"transitRates": []}}))
                    return
            route.continue_()

        page.route("**/graphql", handler)
        booking, scenario = _go_to_booking_step1(page, base_url)
        booking.configure_items(booking.get_challenge_items(scenario))
        booking.select_delivery_date(scenario["deliveryDate"])
        expect(page.get_by_text("No shipping options available")).to_be_visible(timeout=15000)
        page.unroute("**/graphql", handler)

    def test_shows_error_message_when_shipping_rates_api_returns_500(self, page, base_url):
        def handler(route):
            post_data = route.request.post_data
            if post_data:
                body = json.loads(post_data)
                if body.get("operationName") == "GetDeliverByTransitRates":
                    route.fulfill(status=500, body="Internal Server Error")
                    return
            route.continue_()

        page.route("**/graphql", handler)
        booking, scenario = _go_to_booking_step1(page, base_url)
        booking.configure_items(booking.get_challenge_items(scenario))
        booking.select_delivery_date(scenario["deliveryDate"])
        expect(page.get_by_text("No shipping options available")).to_be_visible(timeout=15000)
        page.unroute("**/graphql", handler)

    def test_shows_ground_and_next_day_express_options_when_two_rates_are_mocked(self, page, base_url):
        def handler(route):
            post_data = route.request.post_data
            if post_data:
                body = json.loads(post_data)
                if body.get("operationName") == "GetDeliverByTransitRates":
                    route.fulfill(
                        status=200,
                        headers={"Content-Type": "application/json"},
                        body=json.dumps({"data": {"transitRates": [MOCK_RATE_GROUND, MOCK_RATE_NEXT_DAY_EXPRESS]}}),
                    )
                    return
            route.continue_()

        page.route("**/graphql", handler)
        booking, scenario = _go_to_booking_step1(page, base_url)
        booking.configure_items(booking.get_challenge_items(scenario))
        booking.select_delivery_date(scenario["deliveryDate"])
        expect(booking.shipment_speeds_heading).to_be_visible(timeout=15000)
        expect(page.get_by_role("radio", name="Ground").first).to_be_visible()
        expect(page.get_by_role("radio", name="Next Day Express").first).to_be_visible()
        page.unroute("**/graphql", handler)

    def test_renders_shipping_options_without_crashing_when_all_price_cents_are_zero(self, page, base_url):
        free_ground = dict(MOCK_RATE_GROUND)
        free_ground["itemRates"] = [dict(MOCK_RATE_GROUND["itemRates"][0], priceCents=0, totalPriceCents=0)]
        free_express = dict(MOCK_RATE_NEXT_DAY_EXPRESS)
        free_express["itemRates"] = [dict(MOCK_RATE_NEXT_DAY_EXPRESS["itemRates"][0], priceCents=0, totalPriceCents=0)]

        def handler(route):
            post_data = route.request.post_data
            if post_data:
                body = json.loads(post_data)
                if body.get("operationName") == "GetDeliverByTransitRates":
                    route.fulfill(
                        status=200,
                        headers={"Content-Type": "application/json"},
                        body=json.dumps({"data": {"transitRates": [free_ground, free_express]}}),
                    )
                    return
            route.continue_()

        page.route("**/graphql", handler)
        booking, scenario = _go_to_booking_step1(page, base_url)
        booking.configure_items(booking.get_challenge_items(scenario))
        booking.select_delivery_date(scenario["deliveryDate"])
        expect(booking.shipment_speeds_heading).to_be_visible(timeout=15000)
        expect(page.get_by_role("radio", name="Ground").first).to_be_visible()
        page.unroute("**/graphql", handler)
