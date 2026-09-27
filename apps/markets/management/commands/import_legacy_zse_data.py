import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.markets.models import Counter, Exchange, PriceRecord


class Command(BaseCommand):
    """
    One-off backfill from the old MarketData project's stock_data.db
    (table: stock_data, columns: counter, date, volume, closing_price).
    Historical data only — it stops around 2023-01-19, so it's useful as
    seed/demo data and for growth charts, not as a live feed.

    Usage:
        python manage.py import_legacy_zse_data /path/to/stock_data.db
    """

    help = "Import historical ZSE prices from the legacy stock_data.db SQLite file."

    def add_arguments(self, parser):
        parser.add_argument("db_path", type=str)
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Bulk insert batch size."
        )

    def handle(self, *args, **options):
        db_path = options["db_path"]
        batch_size = options["batch_size"]

        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.Error as exc:
            raise CommandError(f"Could not open {db_path}: {exc}") from exc

        cursor = conn.cursor()
        cursor.execute("SELECT counter, date, volume, closing_price FROM stock_data;")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.stdout.write(self.style.WARNING("No rows found in legacy database."))
            return

        zse, _ = Exchange.objects.get_or_create(code="ZSE", defaults={"name": "Zimbabwe Stock Exchange"})

        counter_cache: dict[str, Counter] = {}
        to_create: list[PriceRecord] = []
        imported, skipped = 0, 0

        with transaction.atomic():
            for counter_name, date_str, volume, price in rows:
                if not counter_name or not date_str:
                    skipped += 1
                    continue

                symbol = counter_name.strip()[:20]
                counter = counter_cache.get(symbol)
                if counter is None:
                    counter, _ = Counter.objects.get_or_create(
                        exchange=zse, symbol=symbol, defaults={"name": counter_name.strip()}
                    )
                    counter_cache[symbol] = counter

                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    closing_price = Decimal(str(price or 0))
                except (ValueError, InvalidOperation):
                    skipped += 1
                    continue

                to_create.append(
                    PriceRecord(
                        counter=counter,
                        date=parsed_date,
                        closing_price=closing_price,
                        volume=int(volume or 0),
                        source="legacy_import",
                    )
                )
                imported += 1

                if len(to_create) >= batch_size:
                    PriceRecord.objects.bulk_create(to_create, ignore_conflicts=True)
                    to_create = []

            if to_create:
                PriceRecord.objects.bulk_create(to_create, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {imported} legacy price records across {len(counter_cache)} counters "
                f"({skipped} rows skipped)."
            )
        )
