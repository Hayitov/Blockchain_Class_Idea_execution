"""SIWE auth endpoints. Verify consumes the nonce and creates the session row in
a single transaction (SELECT ... FOR UPDATE on the nonce), so a replayed nonce
loses the race instead of producing a second session.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.siwe import (
    SiweError,
    make_nonce,
    parse_and_verify,
    session_expiry,
    session_token,
)
from app.db import get_db
from app.models import AuthNonce, Sess, Student
from app.schemas import MeResponse, NonceRequest, NonceResponse, StudentOut, VerifyRequest
from app.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE_NAME = "sid"


def _normalize_address(addr: str) -> str:
    if not addr.startswith("0x") or len(addr) != 42:
        raise HTTPException(status_code=400, detail="invalid eth address")
    return addr.lower()


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.post("/nonce", response_model=NonceResponse)
def issue_nonce(payload: NonceRequest, db: Session = Depends(get_db)) -> NonceResponse:
    address = _normalize_address(payload.address)
    nonce = make_nonce()
    row = AuthNonce(address=address, nonce=nonce)
    db.add(row)
    db.commit()
    db.refresh(row)
    return NonceResponse(nonce=nonce, issued_at=row.created_at)


@router.post("/verify", response_model=MeResponse)
def verify(payload: VerifyRequest, response: Response, db: Session = Depends(get_db)) -> MeResponse:
    try:
        parsed = parse_and_verify(payload.message, payload.signature)
    except SiweError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    address = parsed.address_lower

    nonce_row = db.execute(
        select(AuthNonce).where(AuthNonce.nonce == parsed.nonce).with_for_update()
    ).scalar_one_or_none()

    if nonce_row is None:
        raise HTTPException(status_code=401, detail="unknown nonce")
    if nonce_row.used_at is not None:
        raise HTTPException(status_code=401, detail="nonce already used")
    if nonce_row.address != address:
        raise HTTPException(status_code=401, detail="nonce/address mismatch")
    if datetime.now(timezone.utc) - nonce_row.created_at > timedelta(
        minutes=settings.nonce_ttl_minutes
    ):
        raise HTTPException(status_code=401, detail="nonce expired")

    nonce_row.used_at = datetime.now(timezone.utc)

    token = session_token()
    sess = Sess(token=token, address=address, expires_at=session_expiry())
    db.add(sess)
    db.commit()

    _set_session_cookie(response, token)

    student = db.scalar(select(Student).where(Student.eth_address == address))
    return MeResponse(
        address=address,
        student=StudentOut.model_validate(student) if student else None,
    )


@router.get("/me", response_model=MeResponse)
def me(
    sid: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> MeResponse:
    if not sid:
        raise HTTPException(status_code=401, detail="not authenticated")

    sess = db.scalar(select(Sess).where(Sess.token == sid))
    if sess is None or sess.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="session expired")

    student = db.scalar(select(Student).where(Student.eth_address == sess.address))
    return MeResponse(
        address=sess.address,
        student=StudentOut.model_validate(student) if student else None,
    )


@router.post("/logout")
def logout(
    response: Response,
    sid: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if sid:
        sess = db.scalar(select(Sess).where(Sess.token == sid))
        if sess is not None:
            db.delete(sess)
            db.commit()
    _clear_session_cookie(response)
    return {"status": "ok"}
