"""Network interception utilities for both generic and GraphQL-specific cases."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

log = logging.getLogger("intercept")


class RequestSpy:
    """
    Passively observe requests matching a URL pattern without modifying them.

    This is the Python equivalent of the JS framework's spy-request pattern.
    Calls route.continue_() so the request proceeds normally.
    """

    def __init__(self, page: "Page", url_pattern: str | re.Pattern):
        self._page = page
        self._pattern = url_pattern
        self._calls: list[dict[str, Any]] = []

    def attach(self) -> "RequestSpy":
        self._page.route(self._pattern, self._handler)
        return self

    def detach(self) -> None:
        self._page.unroute(self._pattern, self._handler)

    @property
    def count(self) -> int:
        return len(self._calls)

    @property
    def calls(self) -> list[dict[str, Any]]:
        return list(self._calls)

    @property
    def last_body(self) -> str:
        """Return the post-data of the most recent captured request."""
        if not self._calls:
            return ""
        return self._calls[-1].get("post_data", "")

    def _handler(self, route: "Route") -> None:
        request = route.request
        entry = {
            "method": request.method,
            "url": request.url,
            "post_data": request.post_data or "",
            "headers": dict(request.headers),
        }
        self._calls.append(entry)
        log.debug("SPY: %s %s", request.method, request.url)
        # Let the request through unchanged
        route.continue_()


class MockRoute:
    """
    Intercept requests and return a canned response.

    Equivalent to the JS framework's mock-response pattern.
    """

    def __init__(
        self,
        page: "Page",
        url_pattern: str | re.Pattern,
        *,
        status: int = 200,
        body: str | None = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ):
        self._page = page
        self._pattern = url_pattern
        self._status = status
        self._headers = headers or {"Content-Type": "application/json"}

        if json_body is not None:
            self._body = json.dumps(json_body)
            self._headers.setdefault("Content-Type", "application/json")
        else:
            self._body = body or ""

    def attach(self) -> "MockRoute":
        self._page.route(self._pattern, self._handler)
        return self

    def detach(self) -> None:
        self._page.unroute(self._pattern, self._handler)

    def _handler(self, route: "Route") -> None:
        log.debug("MOCK: %s %s → %s", route.request.method, route.request.url, self._status)
        route.fulfill(
            status=self._status,
            headers=self._headers,
            body=self._body,
        )


class FailureSimulator:
    """
    Simulate network failures for resilience testing.

    Supports:
      - HTTP error codes (e.g. 500, 503)
      - Connection abort (simulates network down)

    Example::

        sim = FailureSimulator(page, "**/api/v1/orders", status=500)
        sim.attach()
        # test shows user-friendly error message
        sim.detach()

        # Or abort the connection entirely:
        sim = FailureSimulator(page, "**/api/v1/orders", abort=True)
        sim.attach()
    """

    def __init__(
        self,
        page: "Page",
        url_pattern: str | re.Pattern,
        *,
        status: int = 500,
        body: str = '{"error": "simulated failure"}',
        abort: bool = False,
    ):
        self._page = page
        self._pattern = url_pattern
        self._status = status
        self._body = body
        self._abort = abort

    def attach(self) -> "FailureSimulator":
        self._page.route(self._pattern, self._handler)
        return self

    def detach(self) -> None:
        self._page.unroute(self._pattern, self._handler)

    def _handler(self, route: "Route") -> None:
        if self._abort:
            log.debug("ABORT: %s %s", route.request.method, route.request.url)
            route.abort("connectionrefused")
        else:
            log.debug("FAIL: %s %s → %s", route.request.method, route.request.url, self._status)
            route.fulfill(
                status=self._status,
                headers={"Content-Type": "application/json"},
                body=self._body,
            )


class GraphQLInterceptor:
    """
    Intercept `/graphql` requests by operation name.

    Mirrors the JavaScript test pattern where route handlers inspect
    `operationName` and only mock selected GraphQL operations.
    """

    def __init__(self, page: "Page", url_pattern: str | re.Pattern = "**/graphql"):
        self._page = page
        self._pattern = url_pattern
        self._operations: dict[str, dict[str, Any]] = {}
        self._captured: list[dict[str, Any]] = []

    def mock_operation(
        self,
        operation_name: str,
        *,
        data: Any,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> "GraphQLInterceptor":
        self._operations[operation_name] = {
            "status": status,
            "headers": headers or {"Content-Type": "application/json"},
            "body": json.dumps({"data": data}),
        }
        return self

    def attach(self) -> "GraphQLInterceptor":
        self._page.route(self._pattern, self._handler)
        return self

    def detach(self) -> None:
        self._page.unroute(self._pattern, self._handler)

    @property
    def captured(self) -> list[dict[str, Any]]:
        return list(self._captured)

    def _handler(self, route: "Route") -> None:
        request = route.request
        post_data = request.post_data or "{}"
        try:
            body = json.loads(post_data)
        except json.JSONDecodeError:
            route.continue_()
            return

        operation_name = body.get("operationName")
        self._captured.append(
            {
                "operation_name": operation_name,
                "url": request.url,
                "body": body,
            }
        )

        mock = self._operations.get(operation_name)
        if mock:
            route.fulfill(
                status=mock["status"],
                headers=mock["headers"],
                body=mock["body"],
            )
            return

        route.continue_()
