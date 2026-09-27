from django.conf import settings
from django.db import models

from apps.markets.models import Counter


class Holding(models.Model):
    """A user's current position in one counter. Quantity is kept in sync via Entry rows."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holdings")
    counter = models.ForeignKey(Counter, on_delete=models.PROTECT, related_name="holdings")
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "counter"], name="unique_holding_per_user_counter")
        ]
        ordering = ("counter__symbol",)

    def __str__(self):
        return f"{self.user.username}: {self.quantity} {self.counter.symbol}"

    def current_value(self):
        latest = self.counter.latest_price()
        if not latest:
            return None
        return latest.closing_price * self.quantity


class Entry(models.Model):
    """
    Every add/remove of shares, recorded with an automatic timestamp — this
    is the source of truth for a Holding's quantity and for gain/loss
    reporting over any date range.
    """

    holding = models.ForeignKey(Holding, on_delete=models.CASCADE, related_name="entries")
    quantity_change = models.IntegerField(help_text="Positive to buy/add, negative to sell/remove.")
    date = models.DateField(auto_now_add=True, db_index=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-date", "-id")

    def __str__(self):
        sign = "+" if self.quantity_change >= 0 else ""
        return f"{self.holding} {sign}{self.quantity_change} on {self.date}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            Holding.objects.filter(pk=self.holding_id).update(
                quantity=models.F("quantity") + self.quantity_change
            )
