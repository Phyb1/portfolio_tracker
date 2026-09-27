from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.markets.models import Counter


class PriceAlert(models.Model):
    ABOVE = "above"
    BELOW = "below"
    DIRECTION_CHOICES = [(ABOVE, "Price rises above"), (BELOW, "Price falls below")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="price_alerts")
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE, related_name="price_alerts")
    target_price = models.DecimalField(max_digits=15, decimal_places=4)
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    is_active = models.BooleanField(default=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        symbol = "≥" if self.direction == self.ABOVE else "≤"
        return f"{self.user.username}: {self.counter.symbol} {symbol} {self.target_price}"

    def is_triggered_by(self, price) -> bool:
        if self.direction == self.ABOVE:
            return price >= self.target_price
        return price <= self.target_price

    def trigger(self):
        self.is_active = False
        self.triggered_at = timezone.now()
        self.save(update_fields=["is_active", "triggered_at"])
