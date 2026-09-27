from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from apps.subscriptions.middleware import PremiumRequiredMixin

from . import services
from .forms import AddHoldingForm
from .models import Entry, Holding


@login_required
def dashboard(request):
    weekly = services.weekly_gain_loss(request.user)
    sheet = services.personalized_price_sheet(request.user)
    context = {
        "weekly": weekly,
        "sheet": sheet,
        "total_value": services.portfolio_value(request.user),
        "profile": request.user.profile,
    }
    return render(request, "portfolio/dashboard.html", context)


@login_required
def add_holding(request):
    if request.method == "POST":
        form = AddHoldingForm(request.POST)
        if form.is_valid():
            counter = form.cleaned_data["counter"]
            quantity = form.cleaned_data["quantity"]
            note = form.cleaned_data["note"]

            holding, _ = Holding.objects.get_or_create(user=request.user, counter=counter)
            # Entry.save() auto-records today's date and updates Holding.quantity.
            Entry.objects.create(holding=holding, quantity_change=quantity, note=note)

            messages.success(request, f"Added {quantity} {counter.symbol} to your portfolio.")
            return redirect("portfolio:dashboard")
    else:
        form = AddHoldingForm()
    return render(request, "portfolio/add_holding.html", {"form": form})


@login_required
def remove_holding(request, holding_id):
    holding = get_object_or_404(Holding, id=holding_id, user=request.user)
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", holding.quantity))
        quantity = min(quantity, holding.quantity)
        if quantity > 0:
            Entry.objects.create(holding=holding, quantity_change=-quantity, note="Removed via dashboard")
            messages.success(request, f"Removed {quantity} {holding.counter.symbol}.")
        return redirect("portfolio:dashboard")
    return render(request, "portfolio/remove_holding.html", {"holding": holding})


@login_required
def report(request):
    """Generate a gain/loss report for an arbitrary date range (query params: start, end)."""
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    end = date.fromisoformat(end_str) if end_str else date.today()
    start = date.fromisoformat(start_str) if start_str else end - services.timedelta(days=7)

    result = services.gain_loss_for_range(request.user, start, end)
    return render(request, "portfolio/report.html", {"result": result})


class PriceSheetView(LoginRequiredMixin, PremiumRequiredMixin, View):
    """Personalized price sheet — gated to trial/subscribers."""

    def get(self, request):
        sheet = services.personalized_price_sheet(request.user)
        return render(request, "portfolio/price_sheet.html", {"sheet": sheet})


@login_required
def portfolio_growth_data(request):
    """JSON series for the overall portfolio growth chart."""
    end = date.today()
    start = end - services.timedelta(days=90)
    points = services.portfolio_growth_series(request.user, start, end)
    return JsonResponse(
        {
            "labels": [p["date"].isoformat() for p in points],
            "values": [float(p["value"]) for p in points],
        }
    )
