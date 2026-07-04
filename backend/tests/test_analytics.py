"""
test_analytics.py — Testes da API de analytics agregada (SPEC 0006/0009).

Três grupos de testes:
1. Feature flag (sem depender de banco): confirmam que ENABLE_ANALYTICS_API
   controla exatamente o status 404 dos três endpoints, via monkeypatch no
   atributo já importado em app.api.v1.routes.analytics.
2. Validação do header X-Session-Id (SPEC 0009): ausente/malformado
   retorna 422, sem depender de banco.
3. Integração com banco (requer PostgreSQL real via DATABASE_URL, mesmo
   padrão de skip gracioso de test_analysis_repository.py — SPEC 0004):
   agregações de summary/skills/timeline e isolamento entre sessões,
   sempre com a flag forçada como ligada via monkeypatch.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

import app.api.v1.routes.analytics as analytics_route
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


@pytest.mark.parametrize(
    "path",
    ["/api/v1/analytics/summary", "/api/v1/analytics/skills", "/api/v1/analytics/timeline"],
)
def test_analytics_returns_404_when_disabled(monkeypatch, path):
    """Com ENABLE_ANALYTICS_API=false, os três endpoints devem responder 404."""
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", False)

    response = client.get(path, headers=_headers())

    assert response.status_code == 404


@pytest.mark.parametrize(
    "path",
    ["/api/v1/analytics/summary", "/api/v1/analytics/skills", "/api/v1/analytics/timeline"],
)
def test_analytics_enabled_flag_stops_returning_404(monkeypatch, path):
    """
    Com ENABLE_ANALYTICS_API=true e um header de sessão válido, a resposta
    não pode mais ser 404 "por causa da flag" — deve ser 200 (banco
    disponível) ou 503 (indisponível).
    """
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", True)

    response = client.get(path, headers=_headers())

    assert response.status_code in (200, 503)


def test_analytics_skills_invalid_status_returns_422(monkeypatch):
    """status fora do enum matched/partial/missing/extra deve retornar 422."""
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", True)

    response = client.get("/api/v1/analytics/skills", params={"status": "nao-existe"}, headers=_headers())

    assert response.status_code == 422


def test_analytics_timeline_invalid_days_returns_422(monkeypatch):
    """days fora do range [1, 365] deve retornar 422."""
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", True)

    response = client.get("/api/v1/analytics/timeline", params={"days": 0}, headers=_headers())

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Testes de validação do header X-Session-Id (SPEC 0009) — não dependem
# de banco.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    ["/api/v1/analytics/summary", "/api/v1/analytics/skills", "/api/v1/analytics/timeline"],
)
def test_analytics_missing_session_header_returns_422(monkeypatch, path):
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", True)

    response = client.get(path)

    assert response.status_code == 422


def test_analytics_summary_malformed_session_header_returns_422(monkeypatch):
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", True)

    response = client.get("/api/v1/analytics/summary", headers={"X-Session-Id": "nao-e-um-uuid"})

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
def analytics_enabled(monkeypatch):
    """Força ENABLE_ANALYTICS_API=true apenas para o teste, revertido automaticamente."""
    monkeypatch.setattr(analytics_route, "ENABLE_ANALYTICS_API", True)


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
    save_analysis(
        db_session,
        b"%PDF-1.4 b",
        "vaga b com bastante texto para passar da validacao",
        None,
        0,
        RESULT_LOW_SCORE,
        session_id,
    )
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
def test_summary_with_empty_database_returns_neutral_values(db_session, analytics_enabled):
    """Com a sessão sem nenhuma análise, /summary deve responder 200 com valores neutros, sem erro."""
    response = client.get("/api/v1/analytics/summary", headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["total_analyses"] == 0
    assert data["average_score"] == 0.0
    assert data["best_score"] == 0
    assert data["worst_score"] == 0
    assert data["total_matched_skills"] == 0
    assert data["total_missing_skills"] == 0
    assert data["most_common_missing_skills"] == []


@_db_required
def test_summary_with_persisted_analyses_computes_correct_metrics(db_session, analytics_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analytics/summary", headers=_headers())
    data = response.json()

    assert response.status_code == 200
    assert data["total_analyses"] == 3
    assert data["best_score"] == 90
    assert data["worst_score"] == 40
    assert data["average_score"] == pytest.approx((90 + 40 + 70) / 3, abs=0.01)
    # matched: python+docker (alta) + python (baixa) = 3 ocorrencias
    assert data["total_matched_skills"] == 3
    # missing: docker+aws (baixa) = 2 ocorrencias
    assert data["total_missing_skills"] == 2
    missing_names = {item["skill_name"] for item in data["most_common_missing_skills"]}
    assert missing_names == {"docker", "aws"}


@_db_required
def test_skills_ranking_without_filter_returns_all_skills_ordered_by_total(db_session, analytics_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analytics/skills", headers=_headers())
    data = response.json()

    assert response.status_code == 200
    skill_names = {item["skill_name"] for item in data["items"]}
    assert skill_names == {"python", "docker", "aws", "english_advanced", "terraform"}

    python_item = next(item for item in data["items"] if item["skill_name"] == "python")
    assert python_item["matched_count"] == 2  # apareceu matched em duas análises
    assert python_item["total_count"] == 2


@_db_required
def test_skills_ranking_with_status_filter(db_session, analytics_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analytics/skills", params={"status": "missing"}, headers=_headers())
    data = response.json()

    assert response.status_code == 200
    skill_names = {item["skill_name"] for item in data["items"]}
    assert skill_names == {"docker", "aws"}
    for item in data["items"]:
        assert item["missing_count"] >= 1


@_db_required
def test_timeline_groups_analyses_by_day(db_session, analytics_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analytics/timeline", headers=_headers())
    data = response.json()

    assert response.status_code == 200
    assert data["days"] == 30
    assert len(data["items"]) == 1  # todas criadas hoje, mesmo dia
    today_item = data["items"][0]
    assert today_item["analyses_count"] == 3
    assert today_item["average_score"] == pytest.approx((90 + 40 + 70) / 3, abs=0.01)


@_db_required
def test_timeline_respects_days_window(db_session, analytics_enabled):
    _seed_three_analyses(db_session)

    response = client.get("/api/v1/analytics/timeline", params={"days": 1}, headers=_headers())
    data = response.json()

    assert response.status_code == 200
    assert data["days"] == 1
    assert len(data["items"]) == 1  # analises de hoje continuam dentro da janela de 1 dia


@_db_required
def test_analytics_responses_never_expose_sensitive_fields(db_session, analytics_enabled):
    _seed_three_analyses(db_session)

    sensitive_keys = {"pdf_sha256", "resume_text_sha256", "description_sha256", "session_id"}

    summary = client.get("/api/v1/analytics/summary", headers=_headers()).json()
    assert sensitive_keys.isdisjoint(summary.keys())

    skills = client.get("/api/v1/analytics/skills", headers=_headers()).json()
    for item in skills["items"]:
        assert sensitive_keys.isdisjoint(item.keys())

    timeline = client.get("/api/v1/analytics/timeline", headers=_headers()).json()
    for item in timeline["items"]:
        assert sensitive_keys.isdisjoint(item.keys())


# ---------------------------------------------------------------------------
# Testes de isolamento entre sessões (SPEC 0009)
# ---------------------------------------------------------------------------


@_db_required
def test_summary_only_reflects_own_session(db_session, analytics_enabled):
    """summary de SESSION_ID não deve contar análises de OTHER_SESSION_ID."""
    _seed_three_analyses(db_session, session_id=OTHER_SESSION_ID)

    response = client.get("/api/v1/analytics/summary", headers=_headers(SESSION_ID))
    data = response.json()

    assert data["total_analyses"] == 0
    assert data["average_score"] == 0.0


@_db_required
def test_skills_ranking_only_reflects_own_session(db_session, analytics_enabled):
    """Ranking de skills de SESSION_ID não deve incluir skills de OTHER_SESSION_ID."""
    _seed_three_analyses(db_session, session_id=OTHER_SESSION_ID)

    response = client.get("/api/v1/analytics/skills", headers=_headers(SESSION_ID))
    data = response.json()

    assert data["items"] == []


@_db_required
def test_timeline_only_reflects_own_session(db_session, analytics_enabled):
    """Timeline de SESSION_ID não deve incluir análises de OTHER_SESSION_ID."""
    _seed_three_analyses(db_session, session_id=OTHER_SESSION_ID)

    response = client.get("/api/v1/analytics/timeline", headers=_headers(SESSION_ID))
    data = response.json()

    assert data["items"] == []
