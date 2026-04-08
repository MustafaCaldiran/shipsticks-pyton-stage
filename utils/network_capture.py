"""Network capture utilities ported from the JavaScript repo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from playwright.sync_api import Page, Request, Response


def is_default_api_call(url: str) -> bool:
    ignored_extensions = (
        ".js",
        ".css",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".map",
    )
    return (
        not any(url.split("?")[0].endswith(ext) for ext in ignored_extensions)
        and "google-analytics" not in url
        and "intercom" not in url
        and "hotjar" not in url
        and "segment" not in url
    )


class NetworkCapture:
    def __init__(
        self,
        page: "Page",
        filter_fn: Callable[[str], bool] = is_default_api_call,
        text_body_limit: int = 800,
    ) -> None:
        self.page = page
        self.filter_fn = filter_fn
        self.text_body_limit = text_body_limit
        self.entries: list[dict[str, Any]] = []
        self._request_handler = None
        self._response_handler = None

    def start(self) -> None:
        def on_request(request: "Request") -> None:
            if not self.filter_fn(request.url):
                return
            self.entries.append(
                {
                    "dir": "REQ",
                    "method": request.method,
                    "url": request.url,
                    "postData": request.post_data,
                }
            )

        def on_response(response: "Response") -> None:
            if not self.filter_fn(response.url):
                return
            body: Any = None
            try:
                body = response.json()
            except Exception:
                try:
                    body = response.text()[: self.text_body_limit]
                except Exception:
                    body = None
            self.entries.append(
                {
                    "dir": "RES",
                    "method": response.request.method,
                    "url": response.url,
                    "status": response.status,
                    "body": body,
                }
            )

        self._request_handler = on_request
        self._response_handler = on_response
        self.page.on("request", on_request)
        self.page.on("response", on_response)

    def stop(self) -> list[dict[str, Any]]:
        if self._request_handler is not None:
            self.page.remove_listener("request", self._request_handler)
        if self._response_handler is not None:
            self.page.remove_listener("response", self._response_handler)
        return list(self.entries)

    def clear(self) -> None:
        self.entries.clear()


def with_network_capture(page: "Page", fn, filter_fn: Callable[[str], bool] = is_default_api_call):
    capture = NetworkCapture(page, filter_fn=filter_fn)
    capture.start()
    try:
        fn()
    finally:
        capture.stop()
    return list(capture.entries)


def save_network_capture(file_path: str | Path, key: str, entries: list[dict[str, Any]]) -> None:
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if output_path.exists():
        try:
            data = json.loads(output_path.read_text())
        except Exception:
            data = {}
    data[key] = entries
    output_path.write_text(json.dumps(data, indent=2))
