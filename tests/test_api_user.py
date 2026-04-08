from __future__ import annotations

import pytest

from data.test_data import get_sign_up_data
from utils.api_helpers import APIHelper


@pytest.mark.api
class TestApiUser:
    def test_post_api_v5_users_creates_user_and_returns_201(self, api_context, base_url):
        helper = APIHelper(api_context, base_url)
        sign_up = get_sign_up_data()
        body = helper.create_user(
            email=sign_up["email"],
            password=sign_up["password"],
            first_name="ApiTest",
            last_name="User",
            phone_number=sign_up["phoneNumber"],
        )

        assert body["email"] == sign_up["email"]
        assert body.get("id")

    def test_post_api_v5_users_duplicate_email_returns_4xx(self, api_context, base_url):
        response = api_context.post(
            f"{base_url}/api/v5/users",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            data={
                "user": {
                    "email": "john@gmail.com",
                    "first_name": "John",
                    "last_name": "Duplicate",
                    "phone_number": "+1 151-351-3515",
                    "country_code": "us",
                    "sms_tracking_optin": False,
                    "hear_about_us": "Influencer",
                    "other_hear_about_us": "",
                    "terms": True,
                    "mobile_verified": False,
                    "brand_id": "shipsticks",
                    "password": "SecurePass123!",
                    "password_confirmation": "SecurePass123!",
                },
                "frontend_app_booking_flow": True,
            },
        )
        assert 400 <= response.status < 500

    def test_post_api_v5_users_missing_required_fields_returns_4xx(self, api_context, base_url):
        response = api_context.post(
            f"{base_url}/api/v5/users",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            data={
                "user": {
                    "email": get_sign_up_data()["email"],
                    "brand_id": "shipsticks",
                    "terms": True,
                },
                "frontend_app_booking_flow": True,
            },
        )
        assert 400 <= response.status < 500

    def test_post_api_v5_users_mismatched_passwords_returns_4xx(self, api_context, base_url):
        response = api_context.post(
            f"{base_url}/api/v5/users",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            data={
                "user": {
                    "email": get_sign_up_data()["email"],
                    "first_name": "ApiTest",
                    "last_name": "User",
                    "phone_number": "+1 151-351-3515",
                    "country_code": "us",
                    "sms_tracking_optin": False,
                    "hear_about_us": "Influencer",
                    "other_hear_about_us": "",
                    "terms": True,
                    "mobile_verified": False,
                    "brand_id": "shipsticks",
                    "password": "SecurePass123!",
                    "password_confirmation": "DifferentPass456!",
                },
                "frontend_app_booking_flow": True,
            },
        )
        assert 400 <= response.status < 500

    def test_new_user_can_authenticate_after_registration(self, api_context, base_url):
        helper = APIHelper(api_context, base_url)
        sign_up = get_sign_up_data()
        helper.create_user(
            email=sign_up["email"],
            password=sign_up["password"],
            first_name="ApiTest",
            last_name="Verify",
            phone_number=sign_up["phoneNumber"],
        )
        helper.login_via_devise(sign_up["email"], sign_up["password"])
        body = helper.graphql(
            operation_name="GetCurrentUser",
            query="""
              query GetCurrentUser {
                user {
                  email
                  firstName
                  lastName
                  id
                }
              }
            """,
        )
        assert body["data"]["user"]["email"] == sign_up["email"]
        assert body["data"]["user"]["firstName"] == "ApiTest"
