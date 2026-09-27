import sqlite3

import pytest
from django.core.management import call_command

from apps.markets.models import Counter, PriceRecord

pytestmark = pytest.mark.django_db


@pytest.fixture
def legacy_db(tmp_path):
    db_path = tmp_path / "stock_data.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE stock_data (counter TEXT, date TEXT, volume REAL, closing_price REAL)"
    )
    conn.executemany(
        "INSERT INTO stock_data VALUES (?, ?, ?, ?)",
        [
            ("Delta", "2021-01-04", 100, 2400.0),
            ("Delta", "2021-01-05", 150, 2410.5),
            ("Econet", "2021-01-04", 5000, 170.0),
            ("BadRow", "not-a-date", 10, 5.0),  # should be skipped
        ],
    )
    conn.commit()
    conn.close()
    return str(db_path)


def test_import_creates_counters_and_prices(legacy_db):
    call_command("import_legacy_zse_data", legacy_db)

    assert Counter.objects.filter(symbol="Delta", exchange__code="ZSE").exists()
    assert Counter.objects.filter(symbol="Econet").exists()
    assert PriceRecord.objects.filter(counter__symbol="Delta").count() == 2


def test_import_skips_unparseable_rows(legacy_db):
    call_command("import_legacy_zse_data", legacy_db)
    assert not Counter.objects.filter(symbol="BadRow").exists()


def test_import_is_idempotent_on_rerun(legacy_db):
    call_command("import_legacy_zse_data", legacy_db)
    call_command("import_legacy_zse_data", legacy_db)  # re-run should not duplicate
    assert PriceRecord.objects.filter(counter__symbol="Delta").count() == 2
