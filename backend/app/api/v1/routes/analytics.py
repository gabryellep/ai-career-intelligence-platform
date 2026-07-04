"""
analytics.py — Rotas de analytics agregada para o dashboard de carreira
(SPEC 0006).

Registradas apenas sob /api/v1 (nunca sem prefixo) — ver app/api/v1/router.py.

Feature flag: ENABLE_ANALYTICS_API (app/core/config.py), desligada por
padrão — separada de ENABLE_HISTORY_API (SPEC 0005) porque analytics expõe
apenas números agregados, nunca um registro individual (ver justificativa
em app/core/config.py). Desde a SPEC 0009, os analytics são isolados por
sessão anônima (X-Session-Id), não mais globais — mas ainda sem
autenticação real (ver PRIVACY.md); por isso ficam desligados em produção
até existir autenticação. Quando desligada, as três rotas respondem 404,
como se não existissem.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import ENABLE_ANALYTICS_API
from app.db.session import get_db
from app.domain.schemas.analytics import (
    AnalyticsSkillsResponse,
    AnalyticsSummaryResponse,
    AnalyticsTimelineResponse,
)
from app.repositories.analytics_repository import get_skills_ranking, get_summary, get_timeline

router = APIRouter()

SkillStatus = Literal["matched", "partial", "missing", "extra"]


def _require_analytics_enabled() -> None:
    if not ENABLE_ANALYTICS_API:
        raise HTTPException(status_code=404, detail="Not Found")


def _analytics_unavailable_error() -> HTTPException:
    return HTTPException(status_code=503, detail="Serviço de analytics temporariamente indisponível.")


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse, summary="Resumo agregado")
def get_summary_route(
    session_id: UUID = Header(..., alias="X-Session-Id"),
    db: Session = Depends(get_db),
):
    """
    Métricas agregadas da sessão informada em X-Session-Id: total de
    análises, score médio/melhor/pior, total de skills matched/missing, e
    as 5 skills mais faltantes.

    Isolado por sessão anônima (SPEC 0009) — X-Session-Id é obrigatório
    (422 se ausente/inválido). Desligado por padrão via ENABLE_ANALYTICS_API.
    Nunca retorna PDF, texto bruto ou hashes.
    """
    _require_analytics_enabled()

    try:
        summary = get_summary(db, session_id)
    except SQLAlchemyError:
        raise _analytics_unavailable_error()

    return AnalyticsSummaryResponse(**summary)


@router.get("/analytics/skills", response_model=AnalyticsSkillsResponse, summary="Ranking de skills")
def get_skills_route(
    session_id: UUID = Header(..., alias="X-Session-Id"),
    status: SkillStatus | None = Query(None, description="Filtra por status: matched, partial, missing ou extra."),
    db: Session = Depends(get_db),
):
    """
    Ranking de skills da sessão informada, por contagem de status
    (matched/partial/missing/extra). Sem filtro, retorna todas as skills
    ordenadas por total_count; com `status`, filtra e ordena pela
    contagem daquele status especificamente.
    """
    _require_analytics_enabled()

    try:
        items = get_skills_ranking(db, session_id, status=status)
    except SQLAlchemyError:
        raise _analytics_unavailable_error()

    return AnalyticsSkillsResponse(items=items)


@router.get("/analytics/timeline", response_model=AnalyticsTimelineResponse, summary="Evolução diária")
def get_timeline_route(
    session_id: UUID = Header(..., alias="X-Session-Id"),
    days: int = Query(30, ge=1, le=365, description="Janela de dias a considerar (padrão 30, máx. 365)."),
    db: Session = Depends(get_db),
):
    """
    Análises da sessão informada, agrupadas por dia (contagem e score
    médio), para os últimos `days` dias. Dias sem nenhuma análise não
    aparecem na lista.
    """
    _require_analytics_enabled()

    try:
        items = get_timeline(db, session_id, days=days)
    except SQLAlchemyError:
        raise _analytics_unavailable_error()

    return AnalyticsTimelineResponse(items=items, days=days)
