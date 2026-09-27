from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from apps.markets.models import Counter, Exchange, PriceRecord
from apps.portfolio.models import Entry, Holding

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="investor", password="pass12345")


@pytest.fixture
def counter():
    exchange = Exchange.objects.create(code="ZSE", name="Zimbabwe Stock Exchange")
    return Counter.objects.create(exchange=exchange, symbol="DLTA", name="Delta Corporation")


def test_one_holding_per_user_per_counter(user, counter):
    Holding.objects.create(user=user, counter=counter, quantity=0)
    with pytest.raises(IntegrityError):
        Holding.objects.create(user=user, counter=counter, quantity=0)


def test_entry_creation_auto_updates_holding_quantity(user, counter):
    holding = Holding.objects.create(user=user, counter=counter, quantity=0)
    Entry.objects.create(holding=holding, quantity_change=100)
    Entry.objects.create(holding=holding, quantity_change=50)
    holding.refresh_from_db()
    assert holding.quantity == 150


def test_entry_can_reduce_quantity(user, counter):
    holding = Holding.objects.create(user=user, counter=counter, quantity=100)
    Entry.objects.create(holding=holding, quantity_change=-40)
    holding.refresh_from_db()
    assert holding.quantity == 60


def test_entry_date_is_recorded_automatically(user, counter):
    holding = Holding.objects.create(user=user, counter=counter, quantity=0)
    entry = Entry.objects.create(holding=holding, quantity_change=10)
    assert entry.date == date.today()


def test_current_value_uses_latest_price(user, counter):
    holding = Holding.objects.create(user=user, counter=counter, quantity=100)
    PriceRecord.objects.create(counter=counter, date=date.today() - timedelta(days=1), closing_price="10.00", volume=1)
    PriceRecord.objects.create(counter=counter, date=date.today(), closing_price="12.50", volume=1)
    assert holding.current_value() == 1250
