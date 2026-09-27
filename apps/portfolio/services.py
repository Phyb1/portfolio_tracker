"""
Reporting logic for the portfolio app: weekly gain/loss, market activity
summaries, personalized price sheets, and portfolio growth over time.
Pulled into plain functions (not stuffed into views) so they're directly
unit-testable without touching HTTP.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from apps.markets.models import PriceRecord

from .models import Holding


def portfolio_value(user, as_of: date | None = None) -> Decimal:
    """Total value of a user's portfolio, valued at the most recent close on/before `as_of`."""
    total = Decimal("0")
    for holding in Holding.objects.filter(user=user, quantity__gt=0).select_related("counter"):
        qs = holding.counter.price_records.all()
        if as_of:
            qs = qs.filter(date__lte=as_of)
        record = qs.order_by("-date").first()
        if record:
            total += record.closing_price * holding.quantity
    return total


def gain_loss_for_range(user, start: date, end: date) -> dict:
    """Total portfolio gain/loss in USD and % between two dates (e.g. a week)."""
    start_value = portfolio_value(user, as_of=start)
    end_value = portfolio_value(user, as_of=end)
    change = end_value - start_value
    pct_change = (change / start_value * 100) if start_value else Decimal("0")
    return {
        "start": start,
        "end": end,
        "start_value": start_value,
        "end_value": end_value,
        "change": change,
        "pct_change": pct_change,
    }


def weekly_gain_loss(user, week_ending: date | None = None) -> dict:
    week_ending = week_ending or date.today()
    week_start = week_ending - timedelta(days=7)
    return gain_loss_for_range(user, week_start, week_ending)


def market_activity_summary(exchange_code: str | None = None, as_of: date | None = None) -> list[dict]:
    """Overview per counter: latest close, quantity traded (volume), and implied trade value."""
    latest_date = as_of
    qs = PriceRecord.objects.select_related("counter", "counter__exchange")
    if exchange_code:
        qs = qs.filter(counter__exchange__code=exchange_code)
    if not latest_date:
        latest_date = qs.order_by("-date").values_list("date", flat=True).first()
    if not latest_date:
        return []

    rows = qs.filter(date=latest_date).order_by("counter__symbol")
    return [
        {
            "counter": r.counter,
            "date": r.date,
            "closing_price": r.closing_price,
            "volume": r.volume,
            "trade_value": r.closing_price * r.volume,
        }
        for r in rows
    ]


def personalized_price_sheet(user) -> list[dict]:
    """The user's holdings with current price, value, and simple metadata — their custom price list."""
    sheet = []
    for holding in Holding.objects.filter(user=user, quantity__gt=0).select_related(
        "counter", "counter__exchange"
    ):
        latest = holding.counter.latest_price()
        sheet.append(
            {
                "holding_id": holding.id,
                "counter": holding.counter,
                "quantity": holding.quantity,
                "price": latest.closing_price if latest else None,
                "value": (latest.closing_price * holding.quantity) if latest else None,
                "as_of": latest.date if latest else None,
            }
        )
    return sheet


def counter_growth_series(counter, start: date | None = None, end: date | None = None):
    """Chronological (date, price) pairs for a counter's growth chart."""
    qs = counter.price_records.order_by("date")
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return list(qs.values_list("date", "closing_price"))


def portfolio_growth_series(user, start: date, end: date, step_days: int = 7):
    """Sampled portfolio value over time, for the overall growth chart."""
    points = []
    current = start
    while current <= end:
        points.append({"date": current, "value": portfolio_value(user, as_of=current)})
        current += timedelta(days=step_days)
    return points
