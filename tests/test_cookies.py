"""Tests for the requests.cookies module, with a focus on the mock classes that
``http.cookiejar`` interacts with.

These tests are intentionally narrow: they exercise the small surface that
``requests.cookies`` exposes to the standard library (the
``MockRequest``/``MockResponse`` shims) so regressions in the contract are
caught at unit-test time, not via a real HTTP roundtrip.
"""

from __future__ import annotations

from email.message import Message

from requests.cookies import MockRequest, MockResponse
from requests import PreparedRequest


def _make_message(headers: list[tuple[str, str]]) -> Message:
    msg = Message()
    for name, value in headers:
        msg[name] = value
    return msg


class TestMockResponse:
    """``MockResponse`` is passed to ``http.cookiejar.CookieJar.extract_cookies``,
    which reads ``info()`` and (in older Python branches) ``getheaders(name)``.
    Both need to return the wrapped value rather than evaluate-and-discard it.
    """

    def test_info_returns_wrapped_headers(self) -> None:
        msg = _make_message([("Set-Cookie", "a=1")])
        response = MockResponse(msg)

        assert response.info() is msg

    def test_getheaders_returns_values_for_name(self) -> None:
        # The body must ``return`` the underlying mapping's headers, not just
        # evaluate the call.  Pre-fix, ``MockResponse.getheaders`` discarded
        # the result and returned ``None`` (and would even raise on a
        # ``dict``-shaped headers because dicts don't have ``.getheaders``).
        msg = _make_message([("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")])
        response = MockResponse(msg)

        assert response.getheaders("Set-Cookie") == ["a=1", "b=2"]

    def test_getheaders_returns_empty_list_for_missing_name(self) -> None:
        # ``http.cookiejar`` callers treat an empty list as "no headers" and
        # iterate without raising; the fix must keep that contract.
        msg = _make_message([("X-Other", "x")])
        response = MockResponse(msg)

        assert response.getheaders("X-Missing") == []

    def test_getheaders_supports_plain_mapping(self) -> None:
        response = MockResponse({"Set-Cookie": "a=1", "X-Other": "x"})

        assert response.getheaders("set-cookie") == ["a=1"]
        assert response.getheaders("X-Missing") == []

    def test_getheaders_supports_bytes_mapping_keys(self) -> None:
        response = MockResponse({b"Set-Cookie": "a=1"})

        assert response.getheaders("set-cookie") == ["a=1"]

    def test_getheaders_supports_legacy_provider(self) -> None:
        class LegacyHeaders:
            def getheaders(self, name: str) -> list[str]:
                return ["a=1"] if name.lower() == "set-cookie" else []

        assert MockResponse(LegacyHeaders()).getheaders("Set-Cookie") == ["a=1"]


class TestMockRequest:
    """Smoke tests for ``MockRequest`` so the small adapter stays consistent."""

    def test_unverifiable_defaults_false(self) -> None:
        prepared = PreparedRequest()
        prepared.prepare(method="GET", url="http://example.com/", headers={})
        request = MockRequest(prepared)

        assert request.get_type() == "http"
        assert request.host == "example.com"
        assert request.origin_req_host == "example.com"
        assert request.get_full_url() == "http://example.com/"
        assert request.get_host() == "example.com"
