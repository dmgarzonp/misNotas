"""Unit tests for AuthService PolicyKit authentication."""

import pytest
from src.services.auth_service import AuthService


def test_auth_service_override_success():
    auth = AuthService(override_auth=True)
    assert auth.authenticate_user("Test Prompt") is True


def test_auth_service_override_failure():
    auth = AuthService(override_auth=False)
    assert auth.authenticate_user("Test Prompt") is False
