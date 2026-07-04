"""add semantic fields to analyses

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-03

Adiciona semantic_score, hybrid_score e semantic_matches (SPEC 0011) à
tabela analyses. Todas nullable, sem server_default: análises existentes
(e novas, enquanto ENABLE_SEMANTIC_MATCHING estiver desligada, que é o
padrão) simplesmente ficam com essas colunas NULL — sem necessidade de
backfill, diferente da SPEC 0009 (session_id era NOT NULL).

semantic_matches guarda apenas nomes de skills (job_skill,
matched_resume_skill) e um float de similaridade — nunca vetores de
embedding.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("semantic_score", sa.Integer(), nullable=True))
    op.add_column("analyses", sa.Column("hybrid_score", sa.Integer(), nullable=True))
    op.add_column("analyses", sa.Column("semantic_matches", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "semantic_matches")
    op.drop_column("analyses", "hybrid_score")
    op.drop_column("analyses", "semantic_score")
