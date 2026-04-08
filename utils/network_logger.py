"""Network logging helpers modeled after the JavaScript utilities."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page, Request, Response

log = logging.getLogger("network")


@dataclass
class NetworkEntry:
    method: str
    url: str
    status: int | None = None
    response_body: str | None = None


class NetworkLogger:
    """Attach to a Playwright page to capture HTTP traffic."""

    def __init__(self, page: "Page"):
        self._page = page
        self._entries: list[NetworkEntry] = []
        self._scoped_entries: list[NetworkEntry] = []
        self._scoping = False
        self._req_handler = None
        self._res_handler = None

    # -- public API ----------------------------------------------------------

    def start(self) -> None:
        """Begin capturing all requests and responses."""
        self._req_handler = self._on_request
        self._res_handler = self._on_response
        self._page.on("request", self._req_handler)
        self._page.on("response", self._res_handler)

    def stop(self) -> None:
        """Stop capturing and detach listeners."""
        if self._req_handler:
            self._page.remove_listener("request", self._req_handler)
        if self._res_handler:
            self._page.remove_listener("response", self._res_handler)

    @property
    def entries(self) -> list[NetworkEntry]:
        return list(self._entries)

    @property
    def scoped_entries(self) -> list[NetworkEntry]:
        return list(self._scoped_entries)

    @contextmanager
    def scoped(self, label: str = "scoped"):
        """Context manager that captures traffic only inside the block."""
        self._scoped_entries.clear()
        self._scoping = True
        log.info("--- [%s] network capture START ---", label)
        try:
            yield self._scoped_entries
        finally:
            self._scoping = False
            log.info(
                "--- [%s] network capture END — %d entries ---",
                label,
                len(self._scoped_entries),
            )

    def save_to_file(self, path: str) -> None:
        """Persist captured traffic to a JSON file."""
        data = [
            {"method": e.method, "url": e.url, "status": e.status}
            for e in self._entries
        ]
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        log.info("Saved %d network entries to %s", len(data), path)

    @staticmethod
    def dump_cookies(context: "BrowserContext") -> list[dict]:
        """Return and log all cookies in the current context."""
        cookies = context.cookies()
        for c in cookies:
            log.debug("Cookie: %s=%s (domain=%s)", c["name"], c["value"][:40], c["domain"])
        return cookies

    # -- internal listeners --------------------------------------------------

    def _on_request(self, request: "Request") -> None:
        entry = NetworkEntry(method=request.method, url=request.url)
        self._entries.append(entry)
        if self._scoping:
            self._scoped_entries.append(entry)
        log.debug(">> %s %s", request.method, request.url)

    def _on_response(self, response: "Response") -> None:
        # Find matching entry by URL (last match)
        for entry in reversed(self._entries):
            if entry.url == response.url and entry.status is None:
                entry.status = response.status
                break
        log.debug("<< %s %s", response.status, response.url)


def _shipsticks_only(url: str) -> bool:
    return "shipsticks" in url.lower()


def _make_handlers(label: str):
    def on_request(request: "Request") -> None:
        url = request.url
        if not _shipsticks_only(url):
            return
        headers = request.headers
        log.info("[%s][REQ] %s %s", label, request.method, url)
        log.info(
            "[%s][REQ] cookie=%s authorization=%s",
            label,
            headers.get("cookie", "(none)")[:400],
            headers.get("authorization", "(none)"),
        )

    def on_response(response: "Response") -> None:
        url = response.url
        if not _shipsticks_only(url):
            return
        headers = response.headers
        marker = "WARN" if response.status >= 300 else "OK"
        location = headers.get("location", "")
        log.info(
            "[%s][RES] %s %s %s%s",
            label,
            marker,
            response.status,
            url,
            f" -> {location}" if location else "",
        )
        if headers.get("set-cookie"):
            log.info("[%s][RES] set-cookie=%s", label, headers["set-cookie"][:400])
        if "/graphql" in url:
            try:
                body = response.json()
                current_user = body.get("data", {}).get("currentUser")
                if current_user is not None:
                    log.info("[%s][RES] currentUser=%s", label, current_user)
            except Exception:
                return

    return on_request, on_response


def attach_network_logging(page: "Page", label: str) -> tuple:
    """Attach persistent request/response loggers to a page."""
    request_handler, response_handler = _make_handlers(label)
    page.on("request", request_handler)
    page.on("response", response_handler)
    return request_handler, response_handler


def detach_network_logging(page: "Page", handlers: tuple) -> None:
    """Detach handlers returned by attach_network_logging()."""
    request_handler, response_handler = handlers
    page.remove_listener("request", request_handler)
    page.remove_listener("response", response_handler)


@contextmanager
def with_network_logging(page: "Page", label: str):
    """Scope network logging to a single block of test steps."""
    handlers = attach_network_logging(page, label)
    try:
        yield
    finally:
        detach_network_logging(page, handlers)


def dump_cookies(context: "BrowserContext", label: str) -> list[dict]:
    """Log all Ship Sticks cookies in the current browser context."""
    relevant = [cookie for cookie in context.cookies() if "shipsticks" in cookie["domain"]]
    log.info("%s", "-" * 70)
    log.info("COOKIES - %s", label)
    log.info("%s", "-" * 70)
    if not relevant:
        log.info("(none)")
        return []
    for cookie in relevant:
        log.info(
            "%s=%s domain=%s path=%s sameSite=%s secure=%s",
            cookie["name"],
            cookie["value"][:80],
            cookie["domain"],
            cookie["path"],
            cookie.get("sameSite"),
            cookie.get("secure"),
        )
    return relevant
