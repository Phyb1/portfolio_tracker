from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Counter, Exchange, PriceRecord


def market_summary(request):
    """Market activity summary: latest close & volume per active counter."""
    exchange_code = request.GET.get("exchange")
    exchanges = Exchange.objects.all()
    latest_date = PriceRecord.objects.order_by("-date").values_list("date", flat=True).first()

    records = PriceRecord.objects.select_related("counter", "counter__exchange")
    if latest_date:
        records = records.filter(date=latest_date)
    if exchange_code:
        records = records.filter(counter__exchange__code=exchange_code)
    records = records.order_by("counter__symbol")

    context = {
        "exchanges": exchanges,
        "selected_exchange": exchange_code,
        "records": records,
        "as_of": latest_date,
    }
    return render(request, "markets/summary.html", context)


def counter_detail(request, exchange_code, symbol):
    counter = get_object_or_404(Counter, exchange__code=exchange_code, symbol=symbol)
    history = counter.price_records.order_by("date")

    context = {
        "counter": counter,
        "history": history,
        "latest": counter.latest_price(),
    }
    return render(request, "markets/counter_detail.html", context)


def counter_chart_data(request, exchange_code, symbol):
    """JSON series for client-side charting (Chart.js) instead of server-rendered matplotlib PNGs."""
    counter = get_object_or_404(Counter, exchange__code=exchange_code, symbol=symbol)
    history = counter.price_records.order_by("date").values_list("date", "closing_price")
    return JsonResponse(
        {
            "symbol": counter.symbol,
            "exchange": counter.exchange.code,
            "labels": [d.isoformat() for d, _ in history],
            "prices": [float(p) for _, p in history],
            "generated_at": timezone.now().isoformat(),
        }
    )
