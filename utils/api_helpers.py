"""API-level helpers aligned with the JavaScript framework's endpoints."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext, Page

log = logging.getLogger("api")


class APIHelper:
    """Thin wrapper around Playwright's request context for Ship Sticks APIs."""

    def __init__(self, request_context: "APIRequestContext", base_url: str):
        self._api = request_context
        self._base_url = base_url.rstrip("/")
        self._csrf_token: str | None = None

    # -- CSRF ----------------------------------------------------------------

    def fetch_csrf_token(self, page: "Page | None" = None, path: str = "/") -> str:
        """Fetch a CSRF token from either a page or an HTTP GET response."""
        token = ""
        if page is not None:
            token = page.evaluate(
                """
                () => {
                    const meta = document.querySelector('meta[name="csrf-token"]');
                    return meta ? meta.getAttribute('content') : null;
                }
                """
            ) or ""
        else:
            html = self._api.get(f"{self._base_url}{path}").text()
            match = re.search(r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"', html)
            token = match.group(1) if match else ""

        if token:
            self._csrf_token = token
            log.debug("CSRF token acquired: %s…", token[:12])
        return token

    def _csrf_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token
        return headers

    # -- User creation -------------------------------------------------------

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str = "John",
        last_name: str = "Doe",
        phone_number: str = "151-351-3515",
        hear_about_us: str = "Influencer",
    ) -> dict:
        payload = {
            "user": {
                "email": email,
                "password": password,
                "password_confirmation": password,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": f"+1 {phone_number}",
                "country_code": "us",
                "hear_about_us": hear_about_us,
                "other_hear_about_us": "",
                "terms": True,
                "mobile_verified": False,
                "brand_id": "shipsticks",
                "sms_tracking_optin": False,
            }
            ,
            "frontend_app_booking_flow": True,
        }
        resp = self._api.post(
            f"{self._base_url}/api/v5/users",
            data=payload,
            headers=self._csrf_headers(),
        )
        log.info("create_user %s → %s", email, resp.status)
        assert resp.ok, f"create_user failed ({resp.status}): {resp.text()}"
        return resp.json()

    # -- GraphQL -------------------------------------------------------------

    def graphql(
        self,
        query: str,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"query": query}
        if operation_name:
            payload["operationName"] = operation_name
        if variables:
            payload["variables"] = variables

        resp = self._api.post(
            f"{self._base_url}/graphql",
            data=payload,
            headers=self._csrf_headers(),
        )
        log.info("graphql → %s", resp.status)
        body = resp.json()
        if "errors" in body:
            log.warning("GraphQL errors: %s", body["errors"])
        return body

    def login_via_devise(self, email: str, password: str) -> None:
        """Authenticate through the same Rails form POST used in JS global setup."""
        csrf_token = self.fetch_csrf_token(path="/users/sign_in")
        assert csrf_token, "CSRF token missing from /users/sign_in"

        response = self._api.post(
            f"{self._base_url}/users/sign_in",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": f"{self._base_url}/users/sign_in",
            },
            data=(
                "utf8=%E2%9C%93"
                f"&authenticity_token={csrf_token}"
                f"&user%5Bemail%5D={email}"
                f"&user%5Bpassword%5D={password}"
                "&user%5Bremember_me%5D=0"
            ),
        )
        assert response.ok, f"Login failed ({response.status}): {response.text()}"

    # -- Generic REST --------------------------------------------------------

    def get(self, path: str, **kwargs) -> dict:
        resp = self._api.get(f"{self._base_url}{path}", **kwargs)
        assert resp.ok, f"GET {path} failed ({resp.status})"
        return resp.json()

    def post(self, path: str, data: dict | None = None, **kwargs) -> dict:
        resp = self._api.post(
            f"{self._base_url}{path}",
            data=data,
            headers=self._csrf_headers(),
            **kwargs,
        )
        assert resp.ok, f"POST {path} failed ({resp.status})"
        return resp.json()
