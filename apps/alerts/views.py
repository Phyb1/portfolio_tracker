from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.subscriptions.middleware import PremiumRequiredMixin

from .forms import PriceAlertForm
from .models import PriceAlert


class AlertListView(LoginRequiredMixin, PremiumRequiredMixin, ListView):
    template_name = "alerts/list.html"
    context_object_name = "alerts"

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user).select_related("counter")


class AlertCreateView(LoginRequiredMixin, PremiumRequiredMixin, CreateView):
    form_class = PriceAlertForm
    template_name = "alerts/form.html"
    success_url = reverse_lazy("alerts:list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Price alert created — we'll email you when it triggers.")
        return super().form_valid(form)


def delete_alert(request, alert_id):
    alert = get_object_or_404(PriceAlert, id=alert_id, user=request.user)
    if request.method == "POST":
        alert.delete()
        messages.success(request, "Alert deleted.")
    return redirect("alerts:list")
