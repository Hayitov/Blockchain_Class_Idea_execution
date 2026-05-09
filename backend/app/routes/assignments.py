from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_student
from app.models import Assignment, Student
from app.schemas import AssignmentOut

router = APIRouter(prefix="/api", tags=["assignments"])


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(
    _: Student = Depends(current_student),  # auth gate; result unused
    db: Session = Depends(get_db),
) -> list[AssignmentOut]:
    rows = db.scalars(select(Assignment).order_by(Assignment.code)).all()
    return [AssignmentOut.model_validate(r) for r in rows]
