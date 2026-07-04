"""
analytics.py — Contratos de resposta da API de analytics agregada (SPEC 0006).

Nenhum destes schemas inclui PDF, texto bruto de currículo/vaga, ou
qualquer hash — apenas métricas agregadas (contagens, médias, rankings de
skills) calculadas sobre os dados já persistidos pela SPEC 0004.
"""

from datetime import date

from pydantic import BaseModel, Field


class MissingSkillCount(BaseModel):
    """Uma skill faltante e quantas vezes ela apareceu como 'missing'."""

    skill_name: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    """Métricas agregadas globais — GET /api/v1/analytics/summary."""

    total_analyses: int = Field(..., ge=0)
    average_score: float = Field(..., ge=0)
    best_score: int = Field(..., ge=0)
    worst_score: int = Field(..., ge=0)
    total_matched_skills: int = Field(..., ge=0)
    total_missing_skills: int = Field(..., ge=0)
    most_common_missing_skills: list[MissingSkillCount] = Field(default_factory=list)


class AnalyticsSkillItem(BaseModel):
    """Ranking de uma skill por status — item de GET /api/v1/analytics/skills."""

    skill_name: str
    matched_count: int = Field(..., ge=0)
    partial_count: int = Field(..., ge=0)
    missing_count: int = Field(..., ge=0)
    extra_count: int = Field(..., ge=0)
    total_count: int = Field(..., ge=0)


class AnalyticsSkillsResponse(BaseModel):
    """Envelope de GET /api/v1/analytics/skills."""

    items: list[AnalyticsSkillItem]


class AnalyticsTimelineItem(BaseModel):
    """Agregação de um dia — item de GET /api/v1/analytics/timeline."""

    date: date
    analyses_count: int = Field(..., ge=0)
    average_score: float = Field(..., ge=0)


class AnalyticsTimelineResponse(BaseModel):
    """Envelope de GET /api/v1/analytics/timeline."""

    items: list[AnalyticsTimelineItem]
    days: int
