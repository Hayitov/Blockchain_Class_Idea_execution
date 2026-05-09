from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class NonceRequest(BaseModel):
    address: str = Field(..., min_length=42, max_length=42)


class NonceResponse(BaseModel):
    nonce: str
    issued_at: datetime


class VerifyRequest(BaseModel):
    message: str
    signature: str


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    eth_address: str
    name: str
    student_id: Optional[str] = None
    github: Optional[str] = None


class MeResponse(BaseModel):
    address: str
    student: Optional[StudentOut] = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    weight: int


class GraderRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    status: str
    score: Optional[int]
    details_json: dict[str, Any]
    created_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    assignment_id: int
    assignment_code: str
    created_at: datetime
    runs: list[GraderRunOut]
