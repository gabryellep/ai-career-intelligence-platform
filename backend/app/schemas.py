"""
schemas.py — Contratos de entrada e saída da API.

Define os modelos Pydantic usados para serialização das respostas HTTP.
Os módulos internos (parser, skills, scorer, recommender) trocam dados
usando tipos Python nativos. O schema Pydantic é usado apenas na camada
de rota para validar e serializar a resposta final.
"""

from pydantic import BaseModel, ConfigDict, Field


class InsightsResponse(BaseModel):
    """Insights sobre o perfil do candidato em relação à vaga."""

    model_config = ConfigDict(from_attributes=True)

    strengths: list[str] = Field(
        default_factory=list,
        description="Pontos fortes do candidato identificados na análise.",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Pontos de atenção ou gaps identificados no perfil.",
    )
    priority_actions: list[str] = Field(
        default_factory=list,
        description="Ações concretas e prioritárias para melhorar a compatibilidade.",
    )


class AnalyzeResponse(BaseModel):
    """
    Resposta do endpoint POST /analyze.

    Contém o resultado completo da análise de compatibilidade
    entre o currículo e a descrição da vaga.
    """

    model_config = ConfigDict(from_attributes=True)

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score de compatibilidade entre currículo e vaga (0 a 100).",
    )
    matched_skills: list[str] = Field(
        ...,
        description="Skills presentes tanto no currículo quanto na descrição da vaga.",
    )
    missing_skills: list[str] = Field(
        ...,
        description="Skills exigidas pela vaga que estão ausentes no currículo.",
    )
    partial_skills: list[str] = Field(
        default_factory=list,
        description="Skills exigidas pela vaga parcialmente atendidas (ex: idioma em nível inferior).",
    )
    extra_skills: list[str] = Field(
        default_factory=list,
        description="Skills do currículo além do exigido pela vaga.",
    )
    match_details: dict = Field(
        default_factory=dict,
        description="Detalhes completos do matching (matched, partial, missing, extra).",
    )
    recommendations: list[str] = Field(
        ...,
        description="Lista de recomendações textuais para melhorar a compatibilidade com a vaga.",
    )
    insights: InsightsResponse = Field(
        default_factory=InsightsResponse,
        description="Insights sobre pontos fortes, fracos e ações prioritárias.",
    )
