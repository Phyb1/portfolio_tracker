# Simple Portfolio Tracker

Track ZSE and VFEX portfolios: enter counters and quantities, get automatic
date-stamped entries, weekly gain/loss reports, market activity summaries,
personalized price sheets, per-counter charts, and overall portfolio growth.
30-day free trial, then $5/quarter via EcoCash (manual, WhatsApp-confirmed)
or Paynow.

## Stack

Django 5, split settings (`config/settings/{base,dev,prod,test}.py`),
python-decouple, WhiteNoise, `passenger_wsgi.py` for cPanel/Passenger,
pytest + pytest-django + factory-boy + freezegun.

## Apps

- `accounts` — auth + `Profile` (30-day trial tracking)
- `markets` — `Exchange` (ZSE/VFEX), `Counter` (handles delisting and
  cross-exchange moves via `status` + `moved_to`), `PriceRecord`
- `portfolio` — `Holding`/`Entry` (auto-dated), gain/loss + market summary +
  price sheet + growth calculations in `services.py`
- `subscriptions` — `Subscription`, manual `EcocashPayment` (WhatsApp
  screenshot confirmation), `PaynowPayment` (direct hashlib SHA512 —
  bypasses known bugs in the `paynow` PyPI SDK)
- `alerts` — `PriceAlert` + `check_alerts` command (emails on trigger)
- `core` — home page, PWA manifest/service worker, sitemap.xml, robots.txt

## ⚠️ Before you rely on this in production

**There is no free live API for ZSE/VFEX prices.** `apps/markets/services/providers.py`
has a pluggable `MarketDataProvider` interface with `ZseProvider`/`VfexProvider`
stubs, but the HTML selectors are placeholders — I had no network access
while building this, so I couldn't inspect the real ZSE/VFEX report pages.
From Termux (which has network):

1. Open the ZSE and VFEX daily market report pages in a browser or `curl`.
2. Check `zse.co.zw` / `vfex.exchange` for the actual "daily trading report"
   URL and table structure (or a CSV/PDF download link, if one exists).
3. Update `REPORT_URL` and the parsing logic in `ZseProvider.fetch()` /
   `VfexProvider.fetch()` to match.
4. Test with `python manage.py fetch_prices` and check the output.

Until that's done, populate prices via Django admin or the legacy import
below.

## First-time setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env   # fill in SECRET_KEY, ECOCASH_RECEIVE_NUMBER, etc.

python manage.py makemigrations accounts markets portfolio subscriptions alerts
python manage.py migrate
python manage.py createsuperuser
```

I couldn't run `makemigrations` or the test suite myself in this build
environment (no network/Django available), so run both yourself after
uploading — `pytest` should be green given the models as written, but flag
anything that isn't and I'll fix it.

### Import your historical ZSE data

Your old `MarketData/zse/stock_data.db` has 26,873 rows through 2023-01-19 —
useful as seed/demo data and for growth charts:

```bash
python manage.py import_legacy_zse_data /path/to/stock_data.db
```

## Running tests

```bash
pytest                      # full suite
pytest apps/portfolio       # one app
pytest --cov=apps           # with coverage
```

## Daily price fetch + alerts (cron)

Add to cPanel "Cron Jobs" (after market close, weekdays):

```
0 18 * * 1-5 cd ~/portfolio_tracker && ./venv/bin/python manage.py fetch_prices >> logs/fetch_prices.log 2>&1
```

This also runs `check_alerts` at the end, so alerts fire the same run.

## Deploying to cPanel/Passenger

Same pattern as your other PHYB projects:

1. Upload the project, create a Python app in cPanel pointing at this
   directory, `passenger_wsgi.py` is the entry point.
2. `pip install -r requirements/prod.txt` in the app's virtualenv.
3. Set `.env` on the server (never commit it).
4. `python manage.py collectstatic --noinput`.
5. If deployed under a subdirectory, set `STATIC_URL`/`MEDIA_URL` in `.env`
   to include the prefix — the explicit `re_path` media route in
   `config/urls.py` and WhiteNoise's manifest storage handle the rest, but
   double-check static files load correctly given the Passenger
   `SCRIPT_NAME`-stripping behavior you hit on the Shato deployment.
6. Make sure `logs/` exists before first request (empty dir won't survive
   git — add a `.gitkeep` or `mkdir -p logs` in your deploy step).

## Payments

- **EcoCash (primary)**: user taps "Pay with EcoCash" → sees your number +
  a reference code → sends payment → taps a WhatsApp deep-link pre-filled
  with the reference → you match the incoming WhatsApp screenshot to the
  `EcocashPayment` record in Django admin and confirm it (there's a bulk
  "Confirm selected" admin action) → subscription activates automatically.
- **Paynow (secondary)**: `PAYNOW_INTEGRATION_ID`/`PAYNOW_INTEGRATION_KEY`
  in `.env` once you have them. Until then the button shows a friendly
  "not configured" error rather than crashing.

## Feature gating

`Profile.has_premium_access` (trial active OR active subscription) is the
single source of truth. `PremiumRequiredMixin` in
`apps/subscriptions/middleware.py` gates alerts and the price sheet;
portfolio dashboard/reports stay free so people always see their own data.
Add the mixin to any future gated view (news, PDF export, etc.) the same way.

## Not yet built (future phases)

- Real ZSE/VFEX scraping (see warning above)
- News feed / PDF downloads as gated features
- PDF export for the price sheet (there's a placeholder link — wire up the
  `pdf` skill or WeasyPrint)
- The `Research` Q&A/community app from your 2021 prototype — could be
  revived as another premium feature
- SEO: sitemap/robots.txt/meta tags are in place; submitting to Google
  Search Console and writing real page copy is still on you
