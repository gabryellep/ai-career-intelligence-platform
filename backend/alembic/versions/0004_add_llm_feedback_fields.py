"""add llm feedback fields to analyses

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-04

Adiciona llm_summary, llm_improvement_plan, llm_study_suggestions e
llm_resume_tips (SPEC 0014) à tabela analyses. Todas nullable, sem
server_default: análises existentes (e novas, enquanto
ENABLE_LLM_FEEDBACK estiver desligada, que é o padrão) simplesmente ficam
com essas colunas NULL — sem necessidade de backfill.

Nunca armazenam o prompt completo enviado ao LLM nem a resposta bruta —
apenas os 4 campos já validados (ver app/services/llm_feedback_service.py).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("llm_summary", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("llm_improvement_plan", postgresql.JSONB(), nullable=True))
    op.add_column("analyses", sa.Column("llm_study_suggestions", postgresql.JSONB(), nullable=True))
    op.add_column("analyses", sa.Column("llm_resume_tips", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "llm_resume_tips")
    op.drop_column("analyses", "llm_study_suggestions")
    op.drop_column("analyses", "llm_improvement_plan")
    op.drop_column("analyses", "llm_summary")
