"""
test_analyses_history.py — Testes da API de histórico (SPEC 0005/0009).

Três grupos de testes:
1. Feature flag (sem depender de banco): confirmam que ENABLE_HISTORY_API
   controla exatamente o status 404 dos endpoints, independentemente da
   variável de ambiente global do processo de testes — usam monkeypatch
   no atributo já importado em app.api.v1.routes.analyses.
2. Validação do header X-Session-Id (SPEC 0009): ausente/malformado
   retorna 422, sem depender de banco.
3. Integração com banco (requer PostgreSQL real via DATABASE_URL, com o
   mesmo padrão de skip gracioso de test_analysis_repository.py — SPEC 0004):
   listagem, paginação, filtros, detalhe e isolamento entre sessões,
   sempre com a flag forçada como ligada via monkeypatch.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

import app.api.v1.routes.analyses as analyses_route
from app.core.config import DATABASE_URL
from app.db.base import Base
from main import app as fastapi_app

client = TestClient(fastapi_app)

SESSION_ID = uuid.uuid4()
OTHER_SESSION_ID = uuid.uuid4()


def _headers(session_id=SESSION_ID):
    return {"X-Session-Id": str(session_id)}


# ---------------------------------------------------------------------------
# Testes de feature flag — não dependem de banco
# ---------------------------------------------------------------------------


def test_list_analyses_returns_404_when_disabled(monkeypatch):
    """Com ENABLE_HISTORY_API=false, GET /api/v1/analyses deve responder 404."""
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", False)

    response = client.get("/api/v1/analyses", headers=_headers())

    assert response.status_code == 404


def test_get_analysis_returns_404_when_disabled(monkeypatch):
    """Com ENABLE_HISTORY_API=false, GET /api/v1/analyses/{id} deve responder 404."""
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", False)

    response = client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000", headers=_headers())

    assert response.status_code == 404


def test_history_enabled_flag_stops_returning_404(monkeypatch):
    """
    Com ENABLE_HISTORY_API=true e um header de sessão válido, a resposta
    não pode mais ser 404 "por causa da flag" — deve ser 200 (banco
    disponível) ou 503 (banco indisponível), nunca 404. Este teste não
    depende de banco estar acessível.
    """
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", True)

    response = client.get("/api/v1/analyses", headers=_headers())

    assert response.status_code in (200, 503)


# ---------------------------------------------------------------------------
# Testes de validação do header X-Session-Id (SPEC 0009) — não dependem
# de banco: a validação de tipo do FastAPI/Pydantic ocorre antes de
# qualquer query.
# ---------------------------------------------------------------------------


def test_list_analyses_missing_session_header_returns_422(monkeypatch):
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", True)

    response = client.get("/api/v1/analyses")

    assert response.status_code == 422


def test_list_analyses_malformed_session_header_returns_422(monkeypatch):
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", True)

    response = client.get("/api/v1/analyses", headers={"X-Session-Id": "nao-e-um-uuid"})

    assert response.status_code == 422


def test_get_analysis_missing_session_header_returns_422(monkeypatch):
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", True)

    response = client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 422


def test_get_analysis_invalid_uuid_returns_422(monkeypatch):
    """Não depende de banco: validação de UUID do path acontece antes de qualquer query."""
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", True)

    response = client.get("/api/v1/analyses/not-a-uuid", headers=_headers())

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Testes de integração com banco real — requerem PostgreSQL via DATABASE_URL
# ---------------------------------------------------------------------------


def _database_available() -> bool:
    try:
        probe_engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with probe_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        probe_engine.dispose()
        return True
    except OperationalError:
        return False


_db_required = pytest.mark.skipif(
    not _database_available(),
    reason="PostgreSQL não disponível em DATABASE_URL — pulando testes de integração de banco.",
)


@pytest.fixture()
def db_session():
    """Garante um schema limpo antes/depois de cada teste (ver SPEC 0004)."""
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def history_enabled(monkeypatch):
    """Força ENABLE_HISTORY_API=true apenas para o teste, revertido automaticamente."""
    monkeypatch.setattr(analyses_route, "ENABLE_HISTORY_API", True)


RESULT_HIGH_SCORE = {
    "score": 90,
    "match_details": {"matched": ["python", "docker"], "partial": [], "missing": [], "extra": []},
    "insights": {"strengths": [], "weaknesses": [], "priority_actions": []},
    "recommendations": ["parabens"],
}
RESULT_LOW_SCORE = {
    "score": 40,
    "match_details": {"matched": ["python"], "partial": [], "missing": ["docker", "aws"], "extra": []},
    "insights": {"strengths": [], "weaknesses": [], "priority_actions": []},
    "recommendations": ["melhore docker e aws"],
}
RESULT_MID_SCORE = {
    "score": 70,
    "match_details": {"matched": [], "partial": ["english_advanced"], "missing": [], "extra": ["terraform"]},
    "insights": {"strengths": [], "weaknesses": [], "priority_actions": []},
    "recommendations": ["melhore ingles"],
}


def _seed_three_analyses(db_session, session_id=SESSION_ID):
    import time

    from app.repositories.analysis_repository import save_analysis

    save_analysis(
        db_session,
        b"%PDF-1.4 a",
        "vaga a com bastante texto para passar da validacao",
        None,
        0,
        RESULT_HIGH_SCORE,
        session_id,
    )
    # Pequena pausa: garante created_at distintos entre as 3 análises.
    # A resolução do relógio pode não ter granularidade suficiente para
    # diferenciar chamadas sucessivas de datetime.now() no mesmo processo
    # (confirmado: duas gravações sem pausa produziram o mesmo created_at
    # até o microssegundo), o que tornaria "mais recente primeiro" não
    # determinístico apenas para efeito deste teste.
    time.sleep(0.01)
    save_analysis(
        db_session,
        b"%PDF-1.4 b",
        "vaga b com bastante texto para passar da validacao",
        None,
        0,
        RESULT_LOW_SCORE,
        session_id,
    )
    time.sleep(0.01)
    save_analysis(
        db_session,
        b"%PDF-1.4 c",
        "vaga c com bastante texto para passar da validacao",
        None,
        0,
        RESULT_MID_SCORE,
        session_id,
    )


@_db_required
def test_list_analyses_returns_persisted_items(db_session, history_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analyses", headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    # mais recente primeiro
    assert data["items"][0]["score"] == 70


@_db_required
def test_list_analyses_pagination(db_session, history_enabled):
    _seed_three_analyses(db_session)

    page1 = client.get("/api/v1/analyses", params={"limit": 2, "offset": 0}, headers=_headers()).json()
    page2 = client.get("/api/v1/analyses", params={"limit": 2, "offset": 2}, headers=_headers()).json()

    assert page1["total"] == 3
    assert len(page1["items"]) == 2
    assert page2["total"] == 3
    assert len(page2["items"]) == 1


@_db_required
def test_list_analyses_min_score_filter(db_session, history_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analyses", params={"min_score": 70}, headers=_headers())
    data = response.json()

    scores = sorted(item["score"] for item in data["items"])
    assert scores == [70, 90]


@_db_required
def test_list_analyses_skill_status_filter(db_session, history_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analyses", params={"skill_status": "missing"}, headers=_headers())
    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["score"] == 40


@_db_required
def test_list_analyses_skill_name_filter(db_session, history_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analyses", params={"skill_name": "docker"}, headers=_headers())
    data = response.json()

    # docker aparece matched (score 90) e missing (score 40)
    scores = sorted(item["score"] for item in data["items"])
    assert scores == [40, 90]


@_db_required
def test_list_analyses_combined_skill_filters(db_session, history_enabled):
    _seed_three_analyses(db_session)

    response = client.get(
        "/api/v1/analyses", params={"skill_status": "missing", "skill_name": "docker"}, headers=_headers()
    )
    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["score"] == 40


@_db_required
def test_list_analyses_never_exposes_sensitive_fields(db_session, history_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analyses", headers=_headers())
    data = response.json()

    sensitive_keys = {
        "pdf_sha256",
        "resume_text_sha256",
        "description_sha256",
        "resume_document_id",
        "job_posting_id",
        "session_id",
    }
    for item in data["items"]:
        assert sensitive_keys.isdisjoint(item.keys())


@_db_required
def test_get_analysis_detail_returns_full_fields(db_session, history_enabled):
    _seed_three_analyses(db_session)

    list_response = client.get("/api/v1/analyses", headers=_headers()).json()
    analysis_id = list_response["items"][0]["id"]

    response = client.get(f"/api/v1/analyses/{analysis_id}", headers=_headers())
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == analysis_id
    assert "match_details" in data
    assert "insights" in data
    assert "recommendations" in data
    sensitive_keys = {"pdf_sha256", "resume_text_sha256", "description_sha256", "session_id"}
    assert sensitive_keys.isdisjoint(data.keys())


@_db_required
def test_get_analysis_detail_not_found_returns_404(db_session, history_enabled):
    response = client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000", headers=_headers())

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Testes de isolamento entre sessões (SPEC 0009)
# ---------------------------------------------------------------------------


@_db_required
def test_session_does_not_see_other_sessions_analyses_in_list(db_session, history_enabled):
    """SESSION_ID não deve ver nenhuma das análises persistidas para OTHER_SESSION_ID."""
    _seed_three_analyses(db_session, session_id=OTHER_SESSION_ID)

    response = client.get("/api/v1/analyses", headers=_headers(SESSION_ID))
    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []


@_db_required
def test_session_cannot_access_other_sessions_analysis_detail(db_session, history_enabled):
    """Detalhe de uma análise de OTHER_SESSION_ID, consultado com header de SESSION_ID, deve ser 404."""
    _seed_three_analyses(db_session, session_id=OTHER_SESSION_ID)

    other_session_list = client.get("/api/v1/analyses", headers=_headers(OTHER_SESSION_ID)).json()
    analysis_id = other_session_list["items"][0]["id"]

    response = client.get(f"/api/v1/analyses/{analysis_id}", headers=_headers(SESSION_ID))

    assert response.status_code == 404


@_db_required
def test_each_session_only_sees_its_own_analyses(db_session, history_enabled):
    """Sessões distintas, cada uma com suas próprias análises, não se misturam na listagem."""
    _seed_three_analyses(db_session, session_id=SESSION_ID)
    _seed_three_analyses(db_session, session_id=OTHER_SESSION_ID)

    response_a = client.get("/api/v1/analyses", headers=_headers(SESSION_ID)).json()
    response_b = client.get("/api/v1/analyses", headers=_headers(OTHER_SESSION_ID)).json()

    assert response_a["total"] == 3
    assert response_b["total"] == 3
    ids_a = {item["id"] for item in response_a["items"]}
    ids_b = {item["id"] for item in response_b["items"]}
    assert ids_a.isdisjoint(ids_b)
