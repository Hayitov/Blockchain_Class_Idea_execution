"""init: students, assignments, auth_nonces, sessions, submissions, grader_runs

Revision ID: 0001_init
Revises:
Create Date: 2026-05-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("eth_address", sa.String(length=42), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("student_id", sa.Text(), nullable=True),
        sa.Column("github", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("eth_address", name="uq_students_eth_address"),
    )
    op.create_index("ix_students_eth_address", "students", ["eth_address"])

    op.create_table(
        "assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "config_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_assignments_code"),
    )
    op.create_index("ix_assignments_code", "assignments", ["code"])

    op.create_table(
        "auth_nonces",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("address", sa.String(length=42), nullable=False),
        sa.Column("nonce", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("nonce", name="uq_auth_nonces_nonce"),
    )
    op.create_index("ix_auth_nonces_nonce", "auth_nonces", ["nonce"])
    op.create_index("ix_auth_nonces_address", "auth_nonces", ["address"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("address", sa.String(length=42), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token", name="uq_sessions_token"),
    )
    op.create_index("ix_sessions_token", "sessions", ["token"])
    op.create_index("ix_sessions_address", "sessions", ["address"])

    op.create_table(
        "submissions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "payload_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], ondelete="CASCADE", name="fk_submissions_student"
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.id"],
            ondelete="CASCADE",
            name="fk_submissions_assignment",
        ),
    )
    op.create_index("ix_submissions_student_id", "submissions", ["student_id"])
    op.create_index("ix_submissions_assignment_id", "submissions", ["assignment_id"])

    op.create_table(
        "grader_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("submission_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column(
            "details_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            ondelete="CASCADE",
            name="fk_grader_runs_submission",
        ),
    )
    op.create_index("ix_grader_runs_submission_id", "grader_runs", ["submission_id"])


def downgrade() -> None:
    op.drop_index("ix_grader_runs_submission_id", table_name="grader_runs")
    op.drop_table("grader_runs")
    op.drop_index("ix_submissions_assignment_id", table_name="submissions")
    op.drop_index("ix_submissions_student_id", table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_sessions_address", table_name="sessions")
    op.drop_index("ix_sessions_token", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_auth_nonces_address", table_name="auth_nonces")
    op.drop_index("ix_auth_nonces_nonce", table_name="auth_nonces")
    op.drop_table("auth_nonces")
    op.drop_index("ix_assignments_code", table_name="assignments")
    op.drop_table("assignments")
    op.drop_index("ix_students_eth_address", table_name="students")
    op.drop_table("students")
