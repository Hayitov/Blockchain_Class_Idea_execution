"""Shared FastAPI dependencies.

Privacy invariant: `current_student` resolves the student row from the
session cookie alone — never from a path or query parameter. This makes
cross-student access structurally impossible at every endpoint that uses
this dependency.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Sess, Student


def current_session(
    sid: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Sess:
    if not sid:
        raise HTTPException(status_code=401, detail="not authenticated")
    sess = db.scalar(select(Sess).where(Sess.token == sid))
    if sess is None or sess.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="session expired")
    return sess


def current_student(
    sess: Sess = Depends(current_session),
    db: Session = Depends(get_db),
) -> Student:
    student = db.scalar(select(Student).where(Student.eth_address == sess.address))
    if student is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "wallet authenticated but no student record found — "
                "contact the course staff to be added to the gradebook"
            ),
        )
    return student
