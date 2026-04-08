"""Low-level interception utility tests that do not depend on the live app UI."""

import pytest

from utils.interception import FailureSimulator, GraphQLInterceptor, MockRoute, RequestSpy


@pytest.mark.network
class TestNetworkInterception:
    def test_spy_captures_requests(self, page):
        spy = RequestSpy(page, "**/anything/graphql").attach()

        page.goto("data:text/html,<html><body>spy</body></html>")
        result = page.evaluate(
            """
            async () => {
                const resp = await fetch('https://httpbin.org/anything/graphql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ operationName: 'Ping' }),
                });
                return resp.json();
            }
            """
        )

        spy.detach()

        assert result["method"] == "POST"
        assert spy.count == 1
        assert '"operationName":"Ping"' in spy.last_body.replace(" ", "")

    def test_mock_returns_canned_response(self, page):
        mock = MockRoute(
            page,
            "**/api/v1/nonexistent",
            json_body={"mocked": True},
            status=200,
        ).attach()

        page.goto("data:text/html,<html><body>mock</body></html>")
        result = page.evaluate(
            """
            async () => {
                const resp = await fetch('https://example.test/api/v1/nonexistent');
                return resp.json();
            }
            """
        )

        mock.detach()
        assert result["mocked"] is True

    def test_failure_simulator_returns_error(self, page):
        fail = FailureSimulator(
            page,
            "**/api/v1/fail-test",
            status=503,
            body='{"error": "service unavailable"}',
        ).attach()

        page.goto("data:text/html,<html><body>failure</body></html>")
        result = page.evaluate(
            """
            async () => {
                const resp = await fetch('https://example.test/api/v1/fail-test');
                return { status: resp.status, body: await resp.json() };
            }
            """
        )

        fail.detach()
        assert result["status"] == 503
        assert result["body"]["error"] == "service unavailable"

    def test_graphql_interceptor_mocks_only_matching_operation(self, page):
        interceptor = (
            GraphQLInterceptor(page)
            .mock_operation("GetCurrentUser", data={"GetCurrentUser": {"email": "user@example.com"}})
            .attach()
        )

        page.goto("data:text/html,<html><body>graphql</body></html>")
        result = page.evaluate(
            """
            async () => {
                const resp = await fetch('https://example.test/graphql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ operationName: 'GetCurrentUser' }),
                });
                return resp.json();
            }
            """
        )

        interceptor.detach()

        assert result["data"]["GetCurrentUser"]["email"] == "user@example.com"
        assert interceptor.captured[0]["operation_name"] == "GetCurrentUser"
