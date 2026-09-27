from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class TrialStatusMiddleware:
    """Attaches a lightweight `has_premium_access` flag to every request for templates."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            request.has_premium_access = request.user.profile.has_premium_access
        else:
            request.has_premium_access = False
        return self.get_response(request)


class PremiumRequiredMixin:
    """
    View mixin for gated features (price alerts, news, PDF exports, price
    sheet downloads). Free during the trial window, then requires an active
    Subscription. Use alongside LoginRequiredMixin.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.profile.has_premium_access:
            messages.info(
                request,
                "Your free trial has ended. Subscribe for $%s/quarter to keep using this feature."
                % settings.SUBSCRIPTION_PRICE_USD,
            )
            return redirect(reverse("subscriptions:plans"))
        return super().dispatch(request, *args, **kwargs)
