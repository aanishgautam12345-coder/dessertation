"""Tests for password reset service."""

import uuid
from unittest.mock import patch, MagicMock

import pytest

from app.services.password_reset import (
    InvalidPasswordError,
    InvalidResetTokenError,
    validate_password,
)


class TestValidatePassword:
    def test_too_short(self):
        with pytest.raises(InvalidPasswordError, match="8 characters"):
            validate_password("Ab1!")

    def test_valid(self):
        validate_password("StrongPass1!")
