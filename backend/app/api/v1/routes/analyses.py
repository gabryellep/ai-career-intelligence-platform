"""
analyses.py — Rotas de leitura do histórico de análises (SPEC 0005).

Registradas apenas sob /api/v1 (nunca sem prefixo) — ver app/api/v1/router.py.

Feature flag: ENABLE_HISTORY_API (app/core/config.py), desligada por padrão.
Sem autenticação, o histórico é isolado por sessão anônima (SPEC 0009),
não por pessoa — por isso essas rotas ficam desligadas em produção até
existir autenticação real (ver PRIVACY.md). Quando desligada, ambas as
rotas respondem 404, como se não existissem.

Sessão anônima (SPEC 0009): X-Session-Id é obrigatório aqui — ausente ou
malformado retorna 422 automaticamente (FastAPI/Pydantic validam o tipo
UUID do parâmetro). Cada sessão só enxerga suas próprias análises.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import ENABLE_HISTORY_API
from app.db.models import Analysis
from app.db.session import get_db
from app.domain.schemas.analysis_history import (
    AnalysisDetailResponse,
    AnalysisListResponse,
    AnalysisSummaryResponse,
)
from app.repositories.analysis_repository import get_analysis_by_id, list_analyses

router = APIRouter()


def _require_history_enabled() -> None:
    if not ENABLE_HISTORY_API:
        raise HTTPException(status_code=404, detail="Not Found")


def _to_summary(analysis: Analysis) -> AnalysisSummaryResponse:
    match_details = analysis.match_details or {}
    return AnalysisSummaryResponse(
        id=analysis.id,
        score=analysis.score,
        matched_skills=match_details.get("matched", []),
        missing_skills=match_details.get("missing", []),
        partial_skills=match_details.get("partial", []),
        extra_skills=match_details.get("extra", []),
        created_at=analysis.created_at,
    )


def _to_detail(analysis: Analysis) -> AnalysisDetailResponse:
    summary = _to_summary(analysis)
    return AnalysisDetailResponse(
        **summary.model_dump(),
        match_details=analysis.match_details or {},
        insights=analysis.insights or {},
        recommendations=analysis.recommendations or [],
    )


@router.get("/analyses", response_model=AnalysisListResponse, summary="Listar análises")
def list_analyses_route(
    session_id: UUID = Header(..., alias="X-Session-Id"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página (máx. 100)."),
    offset: int = Query(0, ge=0, description="Quantidade de itens a pular."),
    min_score: int | None = Query(None, ge=0, le=100, description="Score mínimo (inclusive)."),
    skill_status: str | None = Query(
        None, description="Filtra por status de skill: matched, partial, missing ou extra."
    ),
    skill_name: str | None = Query(None, description="Filtra por nome de skill (ex.: docker)."),
    db: Session = Depends(get_db),
):
    """
    Lista análises da sessão informada em X-Session-Id (mais recentes
    primeiro). Nunca retorna PDF, texto bruto de currículo/vaga, ou
    hashes — apenas score, skills, insights, recomendações e created_at.

    Isolada por sessão anônima (SPEC 0009) — X-Session-Id é obrigatório
    (422 se ausente/inválido). Desligado por padrão via ENABLE_HISTORY_API.
    """
    _require_history_enabled()

    try:
        items, total = list_analyses(
            db,
            session_id=session_id,
            limit=limit,
            offset=offset,
            min_score=min_score,
            skill_status=skill_status,
            skill_name=skill_name,
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Serviço de histórico temporariamente indisponível.")

    return AnalysisListResponse(
        items=[_to_summary(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisDetailResponse,
    summary="Detalhe de uma análise",
)
def get_analysis_route(
    analysis_id: UUID,
    session_id: UUID = Header(..., alias="X-Session-Id"),
    db: Session = Depends(get_db),
):
    """
    Retorna o detalhe completo de uma análise (score, skills, match_details,
    insights, recomendações, created_at) — apenas se pertencer à sessão
    informada em X-Session-Id. Nunca retorna PDF, texto bruto ou hashes.

    404 se o id não existir OU se pertencer a outra sessão (nunca 403 —
    não revela a existência da análise a quem não tem acesso a ela); 404
    também se ENABLE_HISTORY_API=false. X-Session-Id ausente/inválido
    retorna 422.
    """
    _require_history_enabled()

    try:
        analysis = get_analysis_by_id(db, analysis_id, session_id)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Serviço de histórico temporariamente indisponível.")

    if analysis is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")

    return _to_detail(analysis)
