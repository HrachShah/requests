from email.message import Message

from requests.cookies import MockResponse


def test_mock_response_getheaders_handles_message_and_mapping_headers() -> None:
    message = Message()
    message.add_header("Set-Cookie", "session=abc")
    assert MockResponse(message).getheaders("set-cookie") == ["session=abc"]
    assert MockResponse({"Set-Cookie": "session=abc"}).getheaders("set-cookie") == ["session=abc"]
