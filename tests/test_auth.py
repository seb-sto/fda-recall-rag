import pytest
from fastapi import HTTPException

from src.api.auth import verify_api_key


def test_verify_api_key_correct(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    verify_api_key(x_api_key="secret123")  # should not raise


def test_verify_api_key_wrong_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(x_api_key="wrong")
    assert exc_info.value.status_code == 401


def test_verify_api_key_missing_header(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(x_api_key=None)
    assert exc_info.value.status_code == 401
