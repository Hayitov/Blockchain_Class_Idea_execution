"""Submission + grader-run endpoints. Every handler resolves the student via
`current_student` (session cookie); path/query params never carry a student id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_student
from app.graders import ethernaut as ethernaut_grader
from app.graders.base import GraderResult
from app.models import Assignment, GraderRun, Student, Submission
from app.schemas import GraderRunOut, SubmissionOut

router = APIRouter(prefix="/api", tags=["submissions"])


@router.post("/assignments/{code}/submit", response_model=GraderRunOut)
def submit_assignment(
    code: str,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> GraderRunOut:
    assignment = db.scalar(select(Assignment).where(Assignment.code == code))
    if assignment is None:
        raise HTTPException(status_code=404, detail=f"unknown assignment '{code}'")

    submission = Submission(
        student_id=student.id,
        assignment_id=assignment.id,
        payload_json={},
    )
    db.add(submission)
    db.flush()  # populate submission.id without committing yet

    if code == "assignment_2_ethernaut":
        result = ethernaut_grader.run(assignment.config_json, student.eth_address)
    else:
        result = GraderResult(
            status="error",
            score=None,
            details={"error": f"no grader registered for '{code}'"},
        )

    run = GraderRun(
        submission_id=submission.id,
        status=result.status,
        score=result.score,
        details_json=result.details,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return GraderRunOut.model_validate(run)


@router.get("/me/submissions", response_model=list[SubmissionOut])
def my_submissions(
    assignment_code: str | None = None,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[SubmissionOut]:
    stmt = (
        select(Submission, Assignment.code)
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .where(Submission.student_id == student.id)
        .order_by(Submission.created_at.desc())
    )
    if assignment_code is not None:
        stmt = stmt.where(Assignment.code == assignment_code)

    out: list[SubmissionOut] = []
    for sub, code in db.execute(stmt).all():
        out.append(
            SubmissionOut(
                id=sub.id,
                student_id=sub.student_id,
                assignment_id=sub.assignment_id,
                assignment_code=code,
                created_at=sub.created_at,
                runs=[GraderRunOut.model_validate(r) for r in sub.runs],
            )
        )
    return out
