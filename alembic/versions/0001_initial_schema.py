"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-27 20:00:00

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("oblast", sa.String(length=255), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "simulations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("community_id", sa.String(length=36), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("community_id", sa.String(length=36), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("community_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_community_id", "sessions", ["community_id"], unique=False)
    op.create_table(
        "directives",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("issuer_role_id", sa.String(length=100), nullable=False),
        sa.Column("assignee_role_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_directives_assignee_role_id", "directives", ["assignee_role_id"], unique=False)
    op.create_index("ix_directives_session_id", "directives", ["session_id"], unique=False)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_index("ix_directives_session_id", table_name="directives")
    op.drop_index("ix_directives_assignee_role_id", table_name="directives")
    op.drop_table("directives")
    op.drop_index("ix_sessions_community_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("assessments")
    op.drop_table("simulations")
    op.drop_table("communities")
