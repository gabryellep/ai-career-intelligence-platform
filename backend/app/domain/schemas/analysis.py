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


class SemanticMatch(BaseModel):
    """
    Uma aproximação semântica entre uma skill exigida pela vaga (não
    encontrada por regra) e uma skill extra do currículo (SPEC 0011).
    """

    model_config = ConfigDict(from_attributes=True)

    job_skill: str = Field(..., description="Skill exigida pela vaga, não encontrada por matching exato.")
    matched_resume_skill: str = Field(..., description="Skill do currículo considerada semanticamente equivalente.")
    similarity: float = Field(
        ..., ge=0.0, le=1.0, description="Similaridade de cosseno entre os embeddings das duas skills (0 a 1)."
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
    semantic_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Score calculado incluindo aproximações semânticas via embeddings (SPEC 0011). "
            "Ausente na resposta (não apenas null) quando ENABLE_SEMANTIC_MATCHING está desligada "
            "ou quando o serviço de embeddings falha — response_model_exclude_none garante que a "
            "resposta fica idêntica ao contrato anterior a esta Spec nesses casos."
        ),
    )
    hybrid_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Combinação de 70% score determinístico + 30% semantic_score (SPEC 0011). "
            "Mesma regra de ausência do semantic_score."
        ),
    )
    semantic_matches: list[SemanticMatch] | None = Field(
        default=None,
        description=(
            "Até 10 aproximações semânticas entre skills faltantes e skills extras do currículo "
            "(SPEC 0011), ordenadas por similaridade decrescente. Mesma regra de ausência do semantic_score."
        ),
    )
    llm_summary: str | None = Field(
        default=None,
        description=(
            "Parágrafo curto explicando o resultado, gerado por um LLM local via Ollama (SPEC 0014). "
            "Ausente na resposta (não apenas null) quando ENABLE_LLM_FEEDBACK está desligada, quando o "
            "Ollama está indisponível/timeout, ou quando a resposta do modelo não valida — nunca decide "
            "score/matching, apenas explica o resultado já calculado."
        ),
    )
    llm_improvement_plan: list[str] | None = Field(
        default=None,
        description=(
            "Até 5 passos priorizados de melhoria, em prosa mais natural (SPEC 0014). "
            "Mesma regra de ausência do llm_summary."
        ),
    )
    llm_study_suggestions: list[str] | None = Field(
        default=None,
        description=(
            "Até 5 sugestões de estudo/prática para as skills faltantes (SPEC 0014). "
            "Mesma regra de ausência do llm_summary."
        ),
    )
    llm_resume_tips: list[str] | None = Field(
        default=None,
        description=(
            "Até 5 dicas de como apresentar melhor o currículo para a vaga — nunca uma reescrita do "
            "currículo em si (SPEC 0014). Mesma regra de ausência do llm_summary."
        ),
    )
