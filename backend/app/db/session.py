"""
session.py — Engine e sessão do SQLAlchemy.

O AnalysisService abre sua própria sessão via get_session() (context manager),
sem depender de FastAPI Depends nesta etapa — mantém a assinatura da rota
POST /analyze inalterada. Ver SPEC 0004, decisão técnica.

get_db() (SPEC 0005) é uma dependência FastAPI (Depends) usada pelas rotas
de leitura do histórico (app/api/v1/routes/analyses.py). Ao contrário do
caminho de escrita (melhor esforço, falha silenciosa), rotas de leitura
não têm resultado independente do banco para devolver — por isso usam o
padrão idiomático do FastAPI, deixando a rota decidir como responder a
uma falha de conexão (ver SPEC 0005, regra de 503).
"""

from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_URL

# connect_timeout curto: se o Postgres estiver indisponível (comum em
# desenvolvimento manual fora do Docker), falha rápido em vez de travar
# a requisição — a análise continua sendo retornada normalmente ao
# usuário mesmo assim (ver AnalysisService._persist_analysis).
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """
    Abre uma sessão de banco e garante o fechamento ao final,
    mesmo em caso de exceção. Não faz commit/rollback automático —
    quem usa a sessão é responsável por chamar db.commit()/db.rollback().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    """Dependência FastAPI (Depends) para rotas de leitura — ver docstring do módulo."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
