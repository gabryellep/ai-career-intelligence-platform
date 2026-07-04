"""add session_id to analyses

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-04

Adiciona a coluna session_id (SPEC 0009) à tabela analyses, para isolar
análises por sessão anônima (UUID gerado no frontend, enviado via header
X-Session-Id). Usa um server_default de backfill (UUID nulo) apenas para
satisfazer NOT NULL em linhas pré-existentes; o default é removido ao
final desta mesma migration — toda nova escrita da aplicação sempre
fornece um session_id real (ver app/repositories/analysis_repository.py).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PLACEHOLDER_SESSION_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    # 1. Adiciona a coluna com default de backfill, para não violar
    #    NOT NULL em linhas já existentes na tabela.
    op.add_column(
        "analyses",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=_PLACEHOLDER_SESSION_ID,
        ),
    )

    # 2. Remove o server_default — a partir daqui, a aplicação é sempre
    #    responsável por fornecer um session_id real em cada INSERT.
    op.alter_column("analyses", "session_id", server_default=None)

    # 3. Índice para os filtros de listagem/detalhe/analytics por sessão.
    op.create_index("ix_analyses_session_id", "analyses", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_analyses_session_id", table_name="analyses")
    op.drop_column("analyses", "session_id")
