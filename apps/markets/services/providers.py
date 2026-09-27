"""
Pluggable data providers for daily ZSE/VFEX closing prices.

IMPORTANT — read before relying on this in production:
There is no free official real-time API for either exchange. This module
gives you a clean seam to plug in a real source without touching views,
models, or the management command that calls it. Two realistic options,
in order of preference:

1. Scrape the public daily market report page ZSE/VFEX publish (HTML table
   or PDF). Selectors below are placeholders — this build environment has
   no network access to inspect the live page, so you MUST verify the
   actual markup from your Termux device (which does have network) and
   fill in the real selectors/columns before relying on this in prod.
2. If you get access to a paid data vendor (e.g. a local brokerage feed),
   write a new provider class implementing the same `fetch(date)` contract
   and swap it in in `fetch_prices.py` — no other code changes needed.

Until real scraping is wired up, use the Django admin or the
`import_legacy_zse_data` command (for historical backfill) to populate
PriceRecord rows manually or from CSV.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date as date_type

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class PriceQuote:
    symbol: str
    name: str
    closing_price: float
    volume: int


class MarketDataProvider:
    """Base interface every exchange provider must implement."""

    exchange_code: str = ""
    source_label: str = "manual"

    def fetch(self, for_date: date_type) -> list[PriceQuote]:
        raise NotImplementedError


class ZseProvider(MarketDataProvider):
    exchange_code = "ZSE"
    source_label = "zse_scrape"

    # TODO(phyb): confirm the real daily report URL from the ZSE website
    # (check zse.co.zw for a "market report" / "daily trading report" page)
    # and adjust the parsing below to match its actual HTML structure.
    REPORT_URL = "https://www.zse.co.zw/"

    def fetch(self, for_date: date_type) -> list[PriceQuote]:
        try:
            response = requests.get(self.REPORT_URL, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("ZSE fetch failed for %s", for_date)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        quotes: list[PriceQuote] = []

        # Placeholder parsing logic — replace once the real table structure
        # is confirmed. Left intentionally defensive so a markup change
        # degrades to "no quotes" rather than throwing.
        table = soup.find("table")
        if not table:
            logger.warning("ZSE report table not found — selectors need updating")
            return quotes

        for row in table.find_all("tr")[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cells) < 3:
                continue
            symbol, price_text, volume_text = cells[0], cells[1], cells[2]
            try:
                price = float(price_text.replace(",", ""))
                volume = int(float(volume_text.replace(",", "") or 0))
            except ValueError:
                continue
            quotes.append(PriceQuote(symbol=symbol, name=symbol, closing_price=price, volume=volume))

        return quotes


class VfexProvider(MarketDataProvider):
    exchange_code = "VFEX"
    source_label = "vfex_scrape"

    # TODO(phyb): confirm the real VFEX daily report URL and structure.
    REPORT_URL = "https://vfex.exchange/"

    def fetch(self, for_date: date_type) -> list[PriceQuote]:
        try:
            response = requests.get(self.REPORT_URL, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("VFEX fetch failed for %s", for_date)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        quotes: list[PriceQuote] = []
        table = soup.find("table")
        if not table:
            logger.warning("VFEX report table not found — selectors need updating")
            return quotes

        for row in table.find_all("tr")[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cells) < 3:
                continue
            symbol, price_text, volume_text = cells[0], cells[1], cells[2]
            try:
                price = float(price_text.replace(",", ""))
                volume = int(float(volume_text.replace(",", "") or 0))
            except ValueError:
                continue
            quotes.append(PriceQuote(symbol=symbol, name=symbol, closing_price=price, volume=volume))

        return quotes


def get_providers() -> list[MarketDataProvider]:
    return [ZseProvider(), VfexProvider()]
