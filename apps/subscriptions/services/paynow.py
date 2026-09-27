"""
Direct Paynow mobile integration using hashlib SHA512, per Paynow's spec —
bypassing the `paynow` PyPI package's request-builder (double URL-encoding
bug) and dead code in InitResponse, consistent with the approach used
across other PHYB projects.

Paynow's hash algorithm: concatenate all POST field VALUES (in the order
they're sent, excluding the hash field itself) + the integration key,
uppercase, SHA512 hexdigest.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from urllib.parse import parse_qs

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PAYNOW_INITIATE_URL = "https://www.paynow.co.zw/interface/initiatetransaction"


@dataclass
class PaynowInitResult:
    success: bool
    poll_url: str | None = None
    redirect_url: str | None = None
    error: str | None = None


def _generate_hash(fields: dict, integration_key: str) -> str:
    concatenated = "".join(str(v) for v in fields.values()) + integration_key
    return hashlib.sha512(concatenated.encode("utf-8")).hexdigest().upper()


def initiate_mobile_payment(*, reference: str, amount: str, email: str, phone: str, method: str = "ecocash") -> PaynowInitResult:
    """
    Initiate a Paynow Express Checkout (mobile money) transaction.
    `method` is one of Paynow's mobile money methods, e.g. 'ecocash', 'onemoney'.
    """
    integration_id = settings.PAYNOW_INTEGRATION_ID
    integration_key = settings.PAYNOW_INTEGRATION_KEY

    if not integration_id or not integration_key:
        return PaynowInitResult(success=False, error="Paynow is not configured yet.")

    fields = {
        "id": integration_id,
        "reference": reference,
        "amount": amount,
        "additionalinfo": "Simple Portfolio Tracker subscription",
        "returnurl": settings.PAYNOW_RETURN_URL,
        "resulturl": settings.PAYNOW_RESULT_URL,
        "authemail": email,
        "phone": phone,
        "method": method,
        "status": "Message",
    }
    fields["hash"] = _generate_hash(fields, integration_key)

    try:
        response = requests.post(PAYNOW_INITIATE_URL, data=fields, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Paynow initiate request failed")
        return PaynowInitResult(success=False, error=str(exc))

    parsed = {k: v[0] for k, v in parse_qs(response.text).items()}

    if parsed.get("status", "").lower() == "error":
        return PaynowInitResult(success=False, error=parsed.get("error", "Unknown Paynow error"))

    return PaynowInitResult(
        success=True,
        poll_url=parsed.get("pollurl"),
        redirect_url=parsed.get("browserurl"),
    )


def check_transaction_status(poll_url: str) -> str:
    """Returns Paynow's status string, e.g. 'Paid', 'Created', 'Cancelled'."""
    try:
        response = requests.post(poll_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Paynow poll request failed")
        return "Unknown"

    parsed = {k: v[0] for k, v in parse_qs(response.text).items()}
    return parsed.get("status", "Unknown")
