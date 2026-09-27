from unittest.mock import Mock, patch

import pytest

from apps.subscriptions.services.paynow import (
    check_transaction_status,
    initiate_mobile_payment,
)

pytestmark = pytest.mark.django_db


def test_initiate_mobile_payment_returns_error_when_not_configured(settings):
    settings.PAYNOW_INTEGRATION_ID = ""
    settings.PAYNOW_INTEGRATION_KEY = ""
    result = initiate_mobile_payment(
        reference="ABC123", amount="5.00", email="a@b.com", phone="0771234567"
    )
    assert result.success is False
    assert "not configured" in result.error


@patch("apps.subscriptions.services.paynow.requests.post")
def test_initiate_mobile_payment_parses_success_response(mock_post, settings):
    settings.PAYNOW_INTEGRATION_ID = "1234"
    settings.PAYNOW_INTEGRATION_KEY = "test-key"
    settings.PAYNOW_RETURN_URL = "https://example.com/return"
    settings.PAYNOW_RESULT_URL = "https://example.com/result"

    mock_post.return_value = Mock(
        text="status=Ok&pollurl=https%3A%2F%2Fpaynow.co.zw%2Fpoll%2F123&browserurl=https%3A%2F%2Fpaynow.co.zw%2Fpay%2F123"
    )
    mock_post.return_value.raise_for_status = Mock()

    result = initiate_mobile_payment(
        reference="ABC123", amount="5.00", email="a@b.com", phone="0771234567"
    )

    assert result.success is True
    assert result.poll_url == "https://paynow.co.zw/poll/123"


@patch("apps.subscriptions.services.paynow.requests.post")
def test_initiate_mobile_payment_parses_error_response(mock_post, settings):
    settings.PAYNOW_INTEGRATION_ID = "1234"
    settings.PAYNOW_INTEGRATION_KEY = "test-key"

    mock_post.return_value = Mock(text="status=Error&error=Invalid+reference")
    mock_post.return_value.raise_for_status = Mock()

    result = initiate_mobile_payment(
        reference="ABC123", amount="5.00", email="a@b.com", phone="0771234567"
    )

    assert result.success is False
    assert "Invalid" in result.error


@patch("apps.subscriptions.services.paynow.requests.post")
def test_check_transaction_status_returns_status_field(mock_post):
    mock_post.return_value = Mock(text="status=Paid&amount=5.00")
    mock_post.return_value.raise_for_status = Mock()

    status = check_transaction_status("https://paynow.co.zw/poll/123")
    assert status == "Paid"
