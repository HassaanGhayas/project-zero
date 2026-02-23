import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.mcp.linkedin_server import LinkedInServer


@pytest.fixture
def token_file(tmp_path):
    token = {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}
    f = tmp_path / "token.json"
    f.write_text(json.dumps(token))
    return f


@pytest.fixture
def server(token_file):
    return LinkedInServer(
        client_id="cid",
        client_secret="csecret",
        token_path=token_file,
    )


def test_get_member_urn_returns_urn(server):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"sub": "abc123"}
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        urn = server.get_member_urn()
    assert urn == "urn:li:person:abc123"


def test_post_text_calls_ugcposts(server):
    mock_get = MagicMock()
    mock_get.json.return_value = {"sub": "abc123"}
    mock_get.raise_for_status = MagicMock()
    mock_post = MagicMock()
    mock_post.json.return_value = {"id": "urn:li:share:999"}
    mock_post.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_get):
        with patch("requests.post", return_value=mock_post) as patched_post:
            result = server.post_text("Hello LinkedIn!")
            call_url = patched_post.call_args[0][0]
            assert "ugcPosts" in call_url
    assert result["id"] == "urn:li:share:999"


def test_post_text_raises_on_http_error(server):
    import requests as req
    mock_get = MagicMock()
    mock_get.json.return_value = {"sub": "abc123"}
    mock_get.raise_for_status = MagicMock()
    mock_post = MagicMock()
    mock_post.raise_for_status.side_effect = req.HTTPError("400")
    with patch("requests.get", return_value=mock_get):
        with patch("requests.post", return_value=mock_post):
            with pytest.raises(req.HTTPError):
                server.post_text("test")


def test_verify_credentials_returns_true(server):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"sub": "abc123", "name": "Test"}
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        assert server.verify_credentials() is True


def test_verify_credentials_returns_false_on_error(server):
    import requests as req
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = req.HTTPError("401")
    with patch("requests.get", return_value=mock_resp):
        assert server.verify_credentials() is False
