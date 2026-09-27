import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command

from apps.alerts.models import PriceAlert
from apps.markets.models import Counter, Exchange, PriceRecord

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="investor", password="pass12345", email="investor@example.com")


@pytest.fixture
def counter():
    exchange = Exchange.objects.create(code="ZSE", name="Zimbabwe Stock Exchange")
    return Counter.objects.create(exchange=exchange, symbol="DLTA", name="Delta")


def test_is_triggered_by_above(counter, user):
    alert = PriceAlert.objects.create(user=user, counter=counter, target_price="10.00", direction=PriceAlert.ABOVE)
    assert alert.is_triggered_by(11) is True
    assert alert.is_triggered_by(9) is False


def test_is_triggered_by_below(counter, user):
    alert = PriceAlert.objects.create(user=user, counter=counter, target_price="10.00", direction=PriceAlert.BELOW)
    assert alert.is_triggered_by(9) is True
    assert alert.is_triggered_by(11) is False


def test_check_alerts_command_sends_email_and_deactivates(counter, user):
    PriceAlert.objects.create(user=user, counter=counter, target_price="10.00", direction=PriceAlert.ABOVE)
    PriceRecord.objects.create(counter=counter, date="2026-01-01", closing_price="12.00", volume=1)

    call_command("check_alerts")

    alert = PriceAlert.objects.get()
    assert alert.is_active is False
    assert alert.triggered_at is not None
    assert len(mail.outbox) == 1
    assert "DLTA" in mail.outbox[0].subject


def test_check_alerts_skips_alert_with_no_price_data(counter, user):
    PriceAlert.objects.create(user=user, counter=counter, target_price="10.00", direction=PriceAlert.ABOVE)
    call_command("check_alerts")
    alert = PriceAlert.objects.get()
    assert alert.is_active is True
    assert len(mail.outbox) == 0


def test_check_alerts_does_not_trigger_when_condition_not_met(counter, user):
    PriceAlert.objects.create(user=user, counter=counter, target_price="10.00", direction=PriceAlert.ABOVE)
    PriceRecord.objects.create(counter=counter, date="2026-01-01", closing_price="5.00", volume=1)

    call_command("check_alerts")

    alert = PriceAlert.objects.get()
    assert alert.is_active is True
    assert len(mail.outbox) == 0
