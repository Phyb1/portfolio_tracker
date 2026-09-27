from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    """
    One-to-one extension of Django's built-in User. Keeping auth on the
    stock User model avoids the migration headaches of a custom user model
    while still letting us track trial/subscription status per account.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    trial_started_at = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Profile<{self.user.username}>"

    def save(self, *args, **kwargs):
        if not self.trial_ends_at:
            days = getattr(settings, "TRIAL_PERIOD_DAYS", 30)
            self.trial_ends_at = self.trial_started_at + timedelta(days=days)
        super().save(*args, **kwargs)

    @property
    def is_trial_active(self) -> bool:
        return timezone.now() < self.trial_ends_at

    @property
    def has_active_subscription(self) -> bool:
        return self.user.subscriptions.filter(
            status="active", period_end__gte=timezone.now()
        ).exists()

    @property
    def has_premium_access(self) -> bool:
        """Single source of truth for feature gating across the app."""
        return self.is_trial_active or self.has_active_subscription

    @property
    def days_left_in_trial(self) -> int:
        if not self.is_trial_active:
            return 0
        return max((self.trial_ends_at - timezone.now()).days, 0)
