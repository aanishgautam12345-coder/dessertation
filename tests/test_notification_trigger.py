"""Tests for the notification trigger service."""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.notification_trigger import (
    _trigger_notifications,
    dispatch_notification_async,
    shutdown_executor,
    _get_executor,
)


class _FakeUser:
    def __init__(self, user_id=None):
        self.id = user_id or uuid.uuid4()
        self.email = "test@example.com"
        self.is_active = True


class _FakePrefs:
    def __init__(self, email_enabled=True):
        self.email_enabled = email_enabled


class _FakeDb:
    def __init__(self, user=None, prefs=None):
        self.user = user or _FakeUser()
        self.prefs = prefs or _FakePrefs()
        self.closed = False

    def query(self, model):
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = self.user if hasattr(model, "__name__") and model.__name__ == "User" else self.prefs
        return q

    def close(self):
        self.closed = True


@patch("app.services.notification_trigger.SessionLocal")
@patch("app.agents.notification_agent.NotificationAgent")
def test_trigger_notifications_sends_when_enabled(mock_agent_cls, mock_session_factory):
    user = _FakeUser()
    prefs = _FakePrefs(email_enabled=True)

    mock_session = MagicMock()

    def fake_query(model):
        q = MagicMock()
        if model.__name__ == "User":
            q.filter.return_value.first.return_value = user
        elif model.__name__ == "NotificationPreference":
            q.filter.return_value.first.return_value = prefs
        else:
            q.filter.return_value.first.return_value = None
        return q

    mock_session.query.side_effect = fake_query
    mock_session_factory.return_value = mock_session
    mock_agent_cls.return_value.check_recommendation_updates.return_value = 1

    _trigger_notifications(123)

    mock_agent_cls.assert_called_once_with(mock_session)
    mock_session.close.assert_called_once()


@patch("app.services.notification_trigger.SessionLocal")
def test_trigger_notifications_skips_disabled_user(mock_session_factory):
    mock_session = MagicMock()
    prefs = _FakePrefs(email_enabled=False)
    mock_session.query.return_value.filter.return_value.first.return_value = prefs
    mock_session_factory.return_value = mock_session

    _trigger_notifications(123)

    mock_session.close.assert_called_once()


@patch("app.services.notification_trigger.SessionLocal")
def test_trigger_notifications_handles_missing_user(mock_session_factory):
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session_factory.return_value = mock_session

    _trigger_notifications(999)

    mock_session.close.assert_called_once()


@patch("app.services.notification_trigger.SessionLocal")
def test_trigger_notifications_handles_exception(mock_session_factory):
    mock_session_factory.side_effect = RuntimeError("DB connection failed")

    # Should not raise
    _trigger_notifications(123)


@patch("app.services.notification_trigger._get_executor")
def test_dispatch_notification_async_submits_to_pool(mock_get_executor):
    executor = MagicMock()
    mock_get_executor.return_value = executor
    mock_future = MagicMock()
    executor.submit.return_value = mock_future

    with patch("app.services.notification_trigger.get_settings") as mock_settings:
        mock_settings.return_value = SimpleNamespace(
            smtp_user="user@gmail.com", smtp_password="pass"
        )
        dispatch_notification_async(42)

    executor.submit.assert_called_once()
    mock_future.add_done_callback.assert_called_once()


def test_dispatch_notification_async_skips_when_no_smtp():
    with patch("app.services.notification_trigger.get_settings") as mock_settings:
        mock_settings.return_value = SimpleNamespace(smtp_user="", smtp_password="")
        with patch("app.services.notification_trigger._get_executor") as mock_exec:
            dispatch_notification_async(42)
            mock_exec.assert_not_called()


def test_shutdown_executor_cleans_up():
    import app.services.notification_trigger as mod
    original = mod._executor
    mod._executor = MagicMock()
    shutdown_executor()
    assert mod._executor is None
    mod._executor = original


def test_get_executor_creates_singleton():
    import app.services.notification_trigger as mod
    original = mod._executor
    mod._executor = None
    executor1 = _get_executor()
    executor2 = _get_executor()
    assert executor1 is executor2
    mod._executor = original
