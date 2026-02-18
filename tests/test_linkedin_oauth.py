import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.api.linkedin_oauth import load_token, save_token, is_token_expired, refresh_access_token


def test_load_token_returns_dict(tmp_path):
    token_data = {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}
    f = tmp_path / "token.json"
    f.write_text(json.dumps(token_data))
    result = load_token(f)
    assert result["access_token"] == "tok"


def test_load_token_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_token(tmp_path / "nonexistent.json")


def test_save_token_creates_file(tmp_path):
    token = {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}
    save_token(token, tmp_path / "token.json")
    assert (tmp_path / "token.json").exists()


def test_is_token_expired_true_for_old_token():
    assert is_token_expired({"expires_at": 1000}) is True


def test_is_token_expired_false_for_fresh_token():
    assert is_token_expired({"expires_at": int(time.time()) + 3600}) is False


def test_refresh_access_token_returns_new_token():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "new_tok", "expires_in": 3600}
    with patch("requests.post", return_value=mock_resp):
        result = refresh_access_token(
            {"refresh_token": "ref"}, "client_id", "client_secret"
        )
    assert result["access_token"] == "new_tok"
    assert "expires_at" in result
