from email.message import Message

from requests.cookies import MockResponse


def test_mock_response_getheaders_returns_header_values():
    headers = Message()
    headers.add_header("Set-Cookie", "session=abc")

    response = MockResponse(headers)

    assert response.getheaders("Set-Cookie") == ["session=abc"]
