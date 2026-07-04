"""
analysis_history.py — Contratos de resposta da API de histórico (SPEC 0005).

Nenhum destes schemas inclui PDF, texto bruto de currículo/vaga, ou
qualquer hash — apenas o resultado estruturado já produzido pelo motor
determinístico e persistido pela SPEC 0004 (score, skills, insights,
recomendações, created_at).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.analysis import InsightsResponse


class AnalysisSummaryResponse(BaseModel):
    """Resumo de uma análise — usado na listagem (GET /api/v1/analyses)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    score: int = Field(..., ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)
    created_at: datetime


class AnalysisDetailResponse(AnalysisSummaryResponse):
    """Detalhe completo de uma análise — usado em GET /api/v1/analyses/{id}."""

    match_details: dict = Field(default_factory=dict)
    insights: InsightsResponse = Field(default_factory=InsightsResponse)
    recommendations: list[str] = Field(default_factory=list)


class AnalysisListResponse(BaseModel):
    """Envelope de paginação da listagem de análises."""

    items: list[AnalysisSummaryResponse]
    total: int
    limit: int
    offset: int
