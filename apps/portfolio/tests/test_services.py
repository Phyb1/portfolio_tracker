from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from apps.markets.models import Counter, Exchange, PriceRecord
from apps.portfolio import services
from apps.portfolio.models import Entry, Holding

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="investor", password="pass12345")


@pytest.fixture
def zse():
    return Exchange.objects.create(code="ZSE", name="Zimbabwe Stock Exchange")


@pytest.fixture
def counter(zse):
    return Counter.objects.create(exchange=zse, symbol="DLTA", name="Delta Corporation")


def test_portfolio_value_sums_all_holdings(user, zse):
    c1 = Counter.objects.create(exchange=zse, symbol="DLTA", name="Delta")
    c2 = Counter.objects.create(exchange=zse, symbol="ECO", name="Econet")
    h1 = Holding.objects.create(user=user, counter=c1, quantity=100)
    h2 = Holding.objects.create(user=user, counter=c2, quantity=50)
    PriceRecord.objects.create(counter=c1, date=date.today(), closing_price="10.00", volume=1)
    PriceRecord.objects.create(counter=c2, date=date.today(), closing_price="4.00", volume=1)

    assert services.portfolio_value(user) == Decimal("1200.00")


def test_portfolio_value_zero_with_no_holdings(user):
    assert services.portfolio_value(user) == Decimal("0")


def test_gain_loss_for_range_computes_change_and_percentage(user, counter):
    holding = Holding.objects.create(user=user, counter=counter, quantity=100)
    start = date.today() - timedelta(days=7)
    end = date.today()
    PriceRecord.objects.create(counter=counter, date=start, closing_price="10.00", volume=1)
    PriceRecord.objects.create(counter=counter, date=end, closing_price="12.00", volume=1)

    result = services.gain_loss_for_range(user, start, end)

    assert result["start_value"] == Decimal("1000.00")
    assert result["end_value"] == Decimal("1200.00")
    assert result["change"] == Decimal("200.00")
    assert result["pct_change"] == Decimal("20.00")


def test_gain_loss_handles_zero_start_value_without_dividing_by_zero(user, counter):
    result = services.gain_loss_for_range(user, date.today() - timedelta(days=7), date.today())
    assert result["pct_change"] == Decimal("0")


def test_market_activity_summary_uses_latest_date(zse):
    c1 = Counter.objects.create(exchange=zse, symbol="DLTA", name="Delta")
    PriceRecord.objects.create(counter=c1, date=date.today() - timedelta(days=1), closing_price="9.00", volume=100)
    PriceRecord.objects.create(counter=c1, date=date.today(), closing_price="10.00", volume=200)

    summary = services.market_activity_summary()

    assert len(summary) == 1
    assert summary[0]["closing_price"] == Decimal("10.00")
    assert summary[0]["trade_value"] == Decimal("2000.00")


def test_personalized_price_sheet_reflects_only_users_holdings(user, counter):
    other_user = User.objects.create_user(username="other", password="pass12345")
    Holding.objects.create(user=user, counter=counter, quantity=10)
    Holding.objects.create(user=other_user, counter=counter, quantity=999)
    PriceRecord.objects.create(counter=counter, date=date.today(), closing_price="5.00", volume=1)

    sheet = services.personalized_price_sheet(user)

    assert len(sheet) == 1
    assert sheet[0]["quantity"] == 10
    assert sheet[0]["value"] == Decimal("50.00")
