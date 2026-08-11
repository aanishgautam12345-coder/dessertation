"""Tests for email service."""

import pytest
from unittest.mock import patch, MagicMock
from email.mime.multipart import MIMEMultipart

from app.services.email import (
    _build_digest_html,
    _send_message,
    send_notification_digest,
    send_password_reset_email,
)


class TestSendMessage:
    @patch("app.services.email.smtplib.SMTP")
    def test_send_success(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        msg = MIMEMultipart()
        msg["Subject"] = "Test"
        msg["From"] = "from@example.com"
        msg["To"] = "to@example.com"

        with patch("app.services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                smtp_user="from@example.com",
                smtp_password="pass",
                smtp_host="smtp.example.com",
                smtp_port=587,
                smtp_timeout_seconds=10,
            )
            result = _send_message(msg)
        assert result is True

    def test_no_smtp_config(self):
        with patch("app.services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(smtp_user="", smtp_password="")
            msg = MIMEMultipart()
            result = _send_message(msg)
        assert result is False


class TestBuildDigestHtml:
    def test_basic(self):
        html = _build_digest_html("Alice", [{"title": "Dev", "company": "Co", "match_percentage": 85, "url": "http://example.com"}])
        assert "Alice" in html
        assert "Dev" in html
        assert "85%" in html

    def test_no_name(self):
        html = _build_digest_html(None, [])
        assert "Hi," in html

    def test_multiple_jobs(self):
        jobs = [
            {"title": f"Job {i}", "company": f"Co{i}", "match_percentage": 70 + i, "url": ""}
            for i in range(3)
        ]
        html = _build_digest_html("Bob", jobs)
        assert "Job 0" in html
        assert "Job 2" in html
