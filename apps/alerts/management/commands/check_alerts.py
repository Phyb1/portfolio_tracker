import logging

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from apps.alerts.models import PriceAlert

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Evaluate all active price alerts against each counter's latest price and
    email any that have triggered. Called automatically at the end of
    `fetch_prices`, but can also be run standalone/on its own cron entry.
    """

    help = "Check active price alerts and send email notifications for triggered ones."

    def handle(self, *args, **options):
        triggered_count = 0

        for alert in PriceAlert.objects.filter(is_active=True).select_related("counter", "user"):
            latest = alert.counter.latest_price()
            if not latest:
                continue

            if alert.is_triggered_by(latest.closing_price):
                self._notify(alert, latest.closing_price)
                alert.trigger()
                triggered_count += 1

        self.stdout.write(self.style.SUCCESS(f"{triggered_count} alert(s) triggered and emailed."))

    def _notify(self, alert, price):
        if not alert.user.email:
            logger.warning("Alert %s has no user email — skipping notification.", alert.id)
            return

        direction_text = "risen to" if alert.direction == PriceAlert.ABOVE else "fallen to"
        subject = f"[Portfolio Tracker] {alert.counter.symbol} {direction_text} {price}"
        message = (
            f"Your price alert for {alert.counter.symbol} ({alert.counter.exchange.code}) has triggered.\n\n"
            f"Target: {alert.get_direction_display()} {alert.target_price}\n"
            f"Current price: {price}\n\n"
            "This alert is now inactive. Log in to set a new one."
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [alert.user.email])
        except Exception:
            logger.exception("Failed to send alert email to %s", alert.user.email)
