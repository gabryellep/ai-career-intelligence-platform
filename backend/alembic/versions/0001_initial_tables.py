"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-07-03

Cria as 4 tabelas da SPEC 0004: resume_documents, job_postings, analyses
e analysis_skills. Escrita manualmente (sem --autogenerate) porque não
havia um PostgreSQL acessível no ambiente de implementação — o schema
abaixo espelha exatamente app/db/models.py.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resume_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pdf_sha256", sa.String(length=64), nullable=False),
        sa.Column("resume_text_sha256", sa.String(length=64), nullable=True),
        sa.Column("resume_text_length", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("description_sha256", sa.String(length=64), nullable=False),
        sa.Column("description_length", sa.Integer(), nullable=False),
        sa.Column("extracted_skills", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resume_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_posting_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("match_details", postgresql.JSONB(), nullable=False),
        sa.Column("insights", postgresql.JSONB(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resume_document_id"], ["resume_documents.id"]),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"]),
    )

    op.create_table(
        "analysis_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("analysis_skills")
    op.drop_table("analyses")
    op.drop_table("job_postings")
    op.drop_table("resume_documents")
