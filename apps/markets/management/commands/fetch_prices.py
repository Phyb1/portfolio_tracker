import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.markets.models import Counter, Exchange, PriceRecord
from apps.markets.services.providers import get_providers

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Fetch today's closing prices for every configured exchange and upsert
    them into PriceRecord. Intended to run once daily via cron/cPanel
    "Cron Jobs", after market close, e.g.:

        0 18 * * 1-5 cd ~/portfolio_tracker && ./venv/bin/python manage.py fetch_prices

    Also triggers alert evaluation once new prices land, so alerts fire the
    same run rather than waiting for a separate cron entry.
    """

    help = "Fetch and store today's ZSE/VFEX closing prices from configured providers."

    def handle(self, *args, **options):
        today = timezone.localdate()
        created, updated, skipped = 0, 0, 0

        for provider in get_providers():
            exchange, _ = Exchange.objects.get_or_create(
                code=provider.exchange_code, defaults={"name": provider.exchange_code}
            )
            quotes = provider.fetch(today)
            if not quotes:
                self.stdout.write(
                    self.style.WARNING(f"No quotes returned for {exchange.code} on {today}")
                )
                continue

            for quote in quotes:
                counter, _ = Counter.objects.get_or_create(
                    exchange=exchange,
                    symbol=quote.symbol,
                    defaults={"name": quote.name or quote.symbol},
                )
                if not counter.is_tradeable:
                    skipped += 1
                    continue

                _, was_created = PriceRecord.objects.update_or_create(
                    counter=counter,
                    date=today,
                    defaults={
                        "closing_price": quote.closing_price,
                        "volume": quote.volume,
                        "source": provider.source_label,
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Prices for {today}: {created} created, {updated} updated, {skipped} skipped (non-tradeable)."
            )
        )

        from django.core.management import call_command

        call_command("check_alerts")
