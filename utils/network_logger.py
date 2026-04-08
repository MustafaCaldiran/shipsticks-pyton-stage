"""Network logging helpers matched to the JavaScript framework."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page, Request, Response

log = logging.getLogger("network")


def _shipsticks_only(url: str) -> bool:
    return "shipsticks" in url.lower()


def _make_handlers(label: str):
    def request_handler(request: "Request") -> None:
        url = request.url
        if not _shipsticks_only(url):
            return
        headers = request.headers
        log.info("[%s][REQ] %s %s", label, request.method, url)
        log.info("cookie: %s", headers.get("cookie", "(none)")[:400])
        log.info("authorization: %s", headers.get("authorization", "(none)"))

    def response_handler(response: "Response") -> None:
        url = response.url
        if not _shipsticks_only(url):
            return
        headers = response.headers
        location = headers.get("location", "")
        marker = "WARN" if response.status >= 300 else "OK"
        log.info("[%s][RES] %s %s %s%s", label, marker, response.status, url, f" -> {location}" if location else "")
        set_cookie = headers.get("set-cookie", "")
        if set_cookie:
            log.info("set-cookie: %s", set_cookie[:400])
        if "/graphql" in url:
            try:
                body = response.json()
            except Exception:
                return
            current_user = body.get("data", {}).get("currentUser")
            if current_user is not None:
                log.info("currentUser: %s", current_user)

    return request_handler, response_handler


@contextmanager
def with_network_logging(page: "Page", label: str):
    request_handler, response_handler = _make_handlers(label)
    page.on("request", request_handler)
    page.on("response", response_handler)
    try:
        yield
    finally:
        page.remove_listener("request", request_handler)
        page.remove_listener("response", response_handler)


def attach_network_logging(page: "Page", label: str):
    request_handler, response_handler = _make_handlers(label)
    page.on("request", request_handler)
    page.on("response", response_handler)
    return request_handler, response_handler


def dump_cookies(context: "BrowserContext", label: str) -> list[dict]:
    relevant = [cookie for cookie in context.cookies() if "shipsticks" in cookie["domain"]]
    log.info("%s", "─" * 70)
    log.info("COOKIES — %s", label)
    log.info("%s", "─" * 70)
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
    log.info("%s", "─" * 70)
    return relevant
