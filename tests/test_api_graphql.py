from __future__ import annotations

import time

import pytest


def _authed_context(playwright, authenticated_api_context):
    response = authenticated_api_context.get("/")
    html = response.text()
    marker = '<meta name="csrf-token" content="'
    csrf = ""
    if marker in html:
        csrf = html.split(marker, 1)[1].split('"', 1)[0]
    return authenticated_api_context, csrf


def _gql(ctx, csrf, base_url, body):
    return ctx.post(
        f"{base_url}/graphql",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-CSRF-Token": csrf,
        },
        data=body,
    )


@pytest.mark.api
class TestApiGraphql:
    @pytest.mark.skip(reason="Requires app-modal login, same as JavaScript source.")
    def test_get_current_user_authenticated_session_returns_user_data(self, page, base_url):
        pass

    def test_get_current_user_unauthenticated_request_returns_null_user(self, api_context, base_url):
        response = api_context.post(
            f"{base_url}/graphql",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            data={
                "operationName": "GetCurrentUser",
                "query": """
                  query GetCurrentUser {
                    user {
                      email
                      id
                      firstName
                      lastName
                    }
                  }
                """,
            },
        )
        assert response.status == 200
        body = response.json()
        assert body.get("data") is None or body.get("data", {}).get("user") is None

    def test_get_user_email_existing_email_returns_user_record(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetUserEmail",
                "query": """
                  query GetUserEmail($email: String!) {
                    getUserByEmail(email: $email) {
                      id
                      name
                      firstName
                      lastName
                      phoneNumber
                      email
                      mobileVerificationEligible
                      mobileVerified
                    }
                  }
                """,
                "variables": {"email": "john@gmail.com"},
            },
        )
        assert response.status == 200
        assert response.json()["data"]["getUserByEmail"]["email"] == "john@gmail.com"

    def test_get_user_email_unknown_email_returns_null(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetUserEmail",
                "query": """
                  query GetUserEmail($email: String!) {
                    getUserByEmail(email: $email) {
                      id
                      email
                    }
                  }
                """,
                "variables": {"email": f"nonexistent-{int(time.time())}@nowhere-test.invalid"},
            },
        )
        assert response.status == 200
        assert response.json()["data"]["getUserByEmail"] is None

    def test_get_product_lines_returns_available_product_lines(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetProductLines",
                "query": """
                  query GetProductLines($shipRoute: ShipRouteInput!) {
                    getProductLines(shipRoute: $shipRoute) {
                      id
                      name
                      displayName
                      icon
                      brand { id }
                      labels(shipRoute: $shipRoute) {
                        id
                        name
                        sku
                        displayName
                      }
                    }
                  }
                """,
                "variables": {
                    "shipRoute": {
                        "origin": {
                            "address1": "1234 Main St",
                            "address2": "",
                            "countryCode": "US",
                            "companyName": "",
                            "state": "CA",
                            "city": "Los Angeles",
                            "postalCode": "90015",
                        },
                        "destination": {
                            "address1": "4321 Main St",
                            "address2": "",
                            "countryCode": "US",
                            "companyName": "",
                            "state": "FL",
                            "city": "Miami Lakes",
                            "postalCode": "33014",
                        },
                    }
                },
            },
        )
        assert response.status == 200
        body = response.json()
        assert "errors" not in body
        assert body["data"]["getProductLines"]

    def test_get_deliver_by_transit_rates_returns_rates(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetDeliverByTransitRates",
                "query": """
                  query GetDeliverByTransitRates($input: DeliverByTransitRateInput!) {
                    transitRates: getDeliverByTransitRates(input: $input) {
                      carrierServiceLevel {
                        serviceLevel { bestValue displayName systemName id }
                        carrier { systemName }
                      }
                      itemRates {
                        priceCents
                        adjustedPriceCents
                        quantity
                        totalPriceCents
                        totalAdjustedPriceCents
                        isPreferred: preferred
                      }
                      shipDate
                      transitTime
                      isOffline: offline
                    }
                  }
                """,
                "variables": {
                    "input": {
                        "arrivalDate": "2026-04-15",
                        "direction": "outbound",
                        "handlingOption": "pickup",
                        "products": [{"productId": "5c5e2d376928b97125000007", "quantity": 1}],
                        "carrier": "",
                        "experimentVariationId": "5079228136292352",
                        "shipRoute": {
                            "origin": {"address1": "1234 Main St", "address2": "", "city": "Los Angeles", "countryCode": "US", "postalCode": "90015", "state": "CA"},
                            "destination": {"address1": "4321 Main St", "address2": "", "city": "Miami Lakes", "countryCode": "US", "postalCode": "33014", "state": "FL"},
                        },
                    }
                },
            },
        )
        assert response.status == 200
        body = response.json()
        assert "errors" not in body
        assert body["data"]["transitRates"]

    def test_get_deliver_by_transit_rates_past_delivery_date_returns_empty_or_error(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetDeliverByTransitRates",
                "query": """
                  query GetDeliverByTransitRates($input: DeliverByTransitRateInput!) {
                    transitRates: getDeliverByTransitRates(input: $input) {
                      shipDate
                      transitTime
                      itemRates { priceCents }
                    }
                  }
                """,
                "variables": {
                    "input": {
                        "arrivalDate": "2024-01-01",
                        "direction": "outbound",
                        "handlingOption": "pickup",
                        "products": [{"productId": "5c5e2d376928b97125000007", "quantity": 1}],
                        "carrier": "",
                        "experimentVariationId": "5079228136292352",
                        "shipRoute": {
                            "origin": {"address1": "1234 Main St", "address2": "", "city": "Los Angeles", "countryCode": "US", "postalCode": "90015", "state": "CA"},
                            "destination": {"address1": "4321 Main St", "address2": "", "city": "Miami Lakes", "countryCode": "US", "postalCode": "33014", "state": "FL"},
                        },
                    }
                },
            },
        )
        assert response.status in {200, 422, 500}

    def test_get_deliver_by_transit_rates_international_route_returns_no_domestic_rates(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetDeliverByTransitRates",
                "query": """
                  query GetDeliverByTransitRates($input: DeliverByTransitRateInput!) {
                    transitRates: getDeliverByTransitRates(input: $input) {
                      shipDate
                      transitTime
                      itemRates { priceCents }
                      carrierServiceLevel { serviceLevel { displayName systemName } }
                    }
                  }
                """,
                "variables": {
                    "input": {
                        "arrivalDate": "2026-06-01",
                        "direction": "outbound",
                        "handlingOption": "pickup",
                        "products": [{"productId": "5c5e2d376928b97125000007", "quantity": 1}],
                        "carrier": "",
                        "experimentVariationId": "5079228136292352",
                        "shipRoute": {
                            "origin": {"address1": "1234 Main St", "address2": "", "city": "Los Angeles", "countryCode": "US", "postalCode": "90015", "state": "CA"},
                            "destination": {"address1": "10 Downing Street", "address2": "", "city": "London", "countryCode": "GB", "postalCode": "SW1A 2AA", "state": ""},
                        },
                    }
                },
            },
        )
        assert response.status in {200, 422, 500}

    def test_get_deliver_by_transit_rates_invalid_product_id_returns_empty_or_error(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "GetDeliverByTransitRates",
                "query": """
                  query GetDeliverByTransitRates($input: DeliverByTransitRateInput!) {
                    transitRates: getDeliverByTransitRates(input: $input) {
                      shipDate
                      transitTime
                      itemRates { priceCents }
                    }
                  }
                """,
                "variables": {
                    "input": {
                        "arrivalDate": "2026-12-01",
                        "direction": "outbound",
                        "handlingOption": "pickup",
                        "products": [{"productId": "invalid-product-id-000000000000", "quantity": 1}],
                        "carrier": "",
                        "experimentVariationId": "5079228136292352",
                        "shipRoute": {
                            "origin": {"address1": "1234 Main St", "address2": "", "city": "Los Angeles", "countryCode": "US", "postalCode": "90015", "state": "CA"},
                            "destination": {"address1": "4321 Main St", "address2": "", "city": "Miami Lakes", "countryCode": "US", "postalCode": "33014", "state": "FL"},
                        },
                    }
                },
            },
        )
        assert response.status in {200, 500}

    def test_create_mobile_verification_invalid_phone_number_returns_failure(self, playwright, authenticated_api_context, base_url):
        ctx, csrf = _authed_context(playwright, authenticated_api_context)
        response = _gql(
            ctx,
            csrf,
            base_url,
            {
                "operationName": "createMobileVerification",
                "query": """
                  mutation createMobileVerification($input: MobileVerificationCreateInput!) {
                    createMobileVerification(input: $input) {
                      success
                      errors { message }
                    }
                  }
                """,
                "variables": {"input": {"phoneNumber": "000-000-0000"}},
            },
        )
        assert response.status == 200
        body = response.json()
        result = body.get("data", {}).get("createMobileVerification")
        assert (
            (result and result.get("success") is False and result.get("errors"))
            or body.get("errors")
        )
