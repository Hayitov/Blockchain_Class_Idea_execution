"""SIWE (EIP-4361) helpers wrapping siwe-py.

We use siwe-py >=4.4. Two responsibilities:

  - parse an incoming raw message and verify the signature
  - enforce our local rules: domain matches our SIWE_DOMAIN, the message
    nonce matches the one we issued, and `issued_at` is within NONCE_TTL
    minutes (5 by default).

The atomic nonce-consume + session-create transaction lives in routes.py;
this module exposes pure functions that don't touch the DB.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from siwe import SiweMessage

from app.settings import settings


def make_nonce() -> str:
    return secrets.token_urlsafe(32)


@dataclass(frozen=True)
class ParsedSiwe:
    address: str  # checksummed
    address_lower: str
    nonce: str
    issued_at: datetime
    domain: str


class SiweError(ValueError):
    pass


def parse_and_verify(raw_message: str, signature: str) -> ParsedSiwe:
    """Verify signature + domain + freshness. Nonce equality is checked in the
    route handler under the same transaction that consumes the nonce row.
    """
    try:
        msg = SiweMessage.from_message(message=raw_message)
    except Exception as exc:  # pragma: no cover — siwe error types vary by version
        raise SiweError(f"malformed SIWE message: {exc}") from exc

    if msg.domain != settings.siwe_domain:
        raise SiweError(
            f"domain mismatch: got {msg.domain!r}, expected {settings.siwe_domain!r}"
        )

    issued_at = _parse_iso(msg.issued_at)
    age = datetime.now(timezone.utc) - issued_at
    if age > timedelta(minutes=settings.nonce_ttl_minutes):
        raise SiweError(f"message issued_at is older than {settings.nonce_ttl_minutes} minutes")
    if age < timedelta(minutes=-1):
        raise SiweError("message issued_at is in the future")

    try:
        msg.verify(signature=signature)
    except Exception as exc:
        raise SiweError(f"signature invalid: {exc}") from exc

    address = msg.address
    return ParsedSiwe(
        address=address,
        address_lower=address.lower(),
        nonce=msg.nonce,
        issued_at=issued_at,
        domain=msg.domain,
    )


def _parse_iso(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # EIP-4361 timestamps are ISO 8601 with 'Z' suffix
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
