import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_reference() -> str:
    """Short human-typeable code the user quotes in their EcoCash/WhatsApp message."""
    return secrets.token_hex(4).upper()


class Subscription(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending payment confirmation"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    METHOD_ECOCASH_MANUAL = "ecocash_manual"
    METHOD_PAYNOW = "paynow"
    METHOD_CHOICES = [
        (METHOD_ECOCASH_MANUAL, "EcoCash (manual, WhatsApp confirmation)"),
        (METHOD_PAYNOW, "Paynow"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    reference = models.CharField(max_length=16, unique=True, default=generate_reference)
    amount_usd = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} - {self.reference} ({self.status})"

    def activate(self):
        period_days = getattr(settings, "SUBSCRIPTION_PERIOD_DAYS", 90)
        now = timezone.now()
        self.status = self.STATUS_ACTIVE
        self.period_start = now
        self.period_end = now + timedelta(days=period_days)
        self.activated_at = now
        self.save(update_fields=["status", "period_start", "period_end", "activated_at"])


class EcocashPayment(models.Model):
    """
    Manual payment record: user sends EcoCash to the business number, then
    DMs a screenshot on WhatsApp quoting the Subscription reference code.
    An admin matches the WhatsApp message to this record and confirms it
    here, which activates the subscription. No automated verification —
    this is intentionally a lightweight manual gate for a $5/quarter plan.
    """

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending review"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_REJECTED, "Rejected"),
    ]

    subscription = models.OneToOneField(
        Subscription, on_delete=models.CASCADE, related_name="ecocash_payment"
    )
    sender_phone_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.CharField(max_length=255, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmed_ecocash_payments",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def confirm(self, admin_user):
        self.status = self.STATUS_CONFIRMED
        self.confirmed_by = admin_user
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_by", "confirmed_at"])
        self.subscription.activate()

    def reject(self, admin_user, note=""):
        self.status = self.STATUS_REJECTED
        self.confirmed_by = admin_user
        self.confirmed_at = timezone.now()
        self.admin_note = note
        self.save(update_fields=["status", "confirmed_by", "confirmed_at", "admin_note"])


class PaynowPayment(models.Model):
    """Optional automated path, alongside manual EcoCash. See services/paynow.py."""

    STATUS_CHOICES = [
        ("created", "Created"),
        ("sent", "Sent to Paynow"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]

    subscription = models.OneToOneField(
        Subscription, on_delete=models.CASCADE, related_name="paynow_payment"
    )
    poll_url = models.URLField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="created")
    raw_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_paid(self):
        self.status = "paid"
        self.save(update_fields=["status"])
        self.subscription.activate()
