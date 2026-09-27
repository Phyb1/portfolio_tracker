from django.db import models


class Exchange(models.Model):
    ZSE = "ZSE"
    VFEX = "VFEX"
    CODE_CHOICES = [(ZSE, "Zimbabwe Stock Exchange"), (VFEX, "Victoria Falls Stock Exchange")]

    code = models.CharField(max_length=10, choices=CODE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    currency = models.CharField(
        max_length=3,
        default="ZWG",
        help_text="Settlement currency, e.g. ZWG for ZSE, USD for VFEX.",
    )

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.code


class Counter(models.Model):
    """
    A tradeable security. Zimbabwean counters can be delisted or can move
    between the ZSE and VFEX (e.g. a dual-listing or a full migration), so
    status and cross-references are first-class rather than being inferred
    from gaps in the price history.
    """

    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_DELISTED = "delisted"
    STATUS_MOVED = "moved"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_DELISTED, "Delisted"),
        (STATUS_MOVED, "Moved to another exchange"),
    ]

    exchange = models.ForeignKey(Exchange, on_delete=models.PROTECT, related_name="counters")
    symbol = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=150)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    status_effective_date = models.DateField(
        null=True, blank=True, help_text="Date the current status took effect."
    )
    status_note = models.CharField(max_length=255, blank=True)

    # If a counter moved exchanges (e.g. ZSE -> VFEX) or was superseded by a
    # relisting, this points to the counter that now represents it, so
    # portfolio holdings can be carried forward instead of just breaking.
    moved_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="moved_from"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("symbol",)
        constraints = [
            models.UniqueConstraint(fields=["exchange", "symbol"], name="unique_symbol_per_exchange")
        ]
        indexes = [models.Index(fields=["exchange", "status"])]

    def __str__(self):
        return f"{self.symbol} ({self.exchange.code})"

    @property
    def is_tradeable(self) -> bool:
        return self.status == self.STATUS_ACTIVE

    def latest_price(self):
        return self.price_records.order_by("-date").first()


class PriceRecord(models.Model):
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE, related_name="price_records")
    date = models.DateField(db_index=True)
    closing_price = models.DecimalField(max_digits=15, decimal_places=4)
    volume = models.BigIntegerField(default=0)
    source = models.CharField(
        max_length=20,
        default="manual",
        help_text="Where this record came from, e.g. 'zse_scrape', 'vfex_scrape', 'legacy_import', 'manual'.",
    )

    class Meta:
        ordering = ("-date",)
        constraints = [
            models.UniqueConstraint(fields=["counter", "date"], name="unique_price_per_counter_per_day")
        ]
        indexes = [models.Index(fields=["counter", "date"])]

    def __str__(self):
        return f"{self.counter.symbol} @ {self.date}: {self.closing_price}"
