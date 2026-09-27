import pytest
from django.db import IntegrityError

from apps.markets.models import Counter, Exchange, PriceRecord

pytestmark = pytest.mark.django_db


@pytest.fixture
def zse():
    return Exchange.objects.create(code="ZSE", name="Zimbabwe Stock Exchange")


@pytest.fixture
def vfex():
    return Exchange.objects.create(code="VFEX", name="Victoria Falls Stock Exchange", currency="USD")


def test_counter_unique_per_exchange(zse):
    Counter.objects.create(exchange=zse, symbol="OKZ", name="OK Zimbabwe")
    with pytest.raises(IntegrityError):
        Counter.objects.create(exchange=zse, symbol="OKZ", name="OK Zimbabwe Duplicate")


def test_same_symbol_allowed_on_different_exchange(zse, vfex):
    Counter.objects.create(exchange=zse, symbol="SIMB", name="Simbisa Brands ZSE")
    # Should not raise — same symbol on a different exchange is fine.
    Counter.objects.create(exchange=vfex, symbol="SIMB", name="Simbisa Brands VFEX")


def test_counter_is_tradeable_only_when_active(zse):
    counter = Counter.objects.create(exchange=zse, symbol="ART", name="Art Corp", status=Counter.STATUS_DELISTED)
    assert counter.is_tradeable is False
    counter.status = Counter.STATUS_ACTIVE
    counter.save()
    assert counter.is_tradeable is True


def test_moved_to_tracks_cross_exchange_transfer(zse, vfex):
    old = Counter.objects.create(exchange=zse, symbol="INN", name="Innscor ZSE", status=Counter.STATUS_MOVED)
    new = Counter.objects.create(exchange=vfex, symbol="INN", name="Innscor VFEX")
    old.moved_to = new
    old.save()
    assert old.moved_to == new
    assert new.moved_from.count() == 1


def test_price_record_unique_per_counter_per_day(zse):
    counter = Counter.objects.create(exchange=zse, symbol="DZL", name="Delta")
    PriceRecord.objects.create(counter=counter, date="2026-01-05", closing_price="120.50", volume=1000)
    with pytest.raises(IntegrityError):
        PriceRecord.objects.create(counter=counter, date="2026-01-05", closing_price="121.00", volume=500)


def test_latest_price_returns_most_recent(zse):
    counter = Counter.objects.create(exchange=zse, symbol="ECO", name="Econet")
    PriceRecord.objects.create(counter=counter, date="2026-01-01", closing_price="10.00", volume=1)
    latest = PriceRecord.objects.create(counter=counter, date="2026-01-10", closing_price="12.00", volume=1)
    assert counter.latest_price() == latest
