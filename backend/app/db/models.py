"""
models.py — Models SQLAlchemy da SPEC 0004.

Decisões de privacidade (ver PRIVACY.md e SPEC 0008/0004):
    - O PDF bruto do currículo NUNCA é armazenado em nenhuma coluna.
    - O texto completo do currículo e da descrição da vaga NUNCA é
      armazenado — apenas hash (SHA-256) e metadados (comprimento).
    - Skills extraídas da vaga (extracted_skills) não são dado pessoal —
      são apenas nomes de tecnologias, seguras para persistir.

AnalysisSkill é uma denormalização deliberada de match_details (que já
vive como JSONB em Analysis): uma linha por skill, preparada para consultas
agregadas futuras (ex.: dashboard da SPEC 0006). Nenhum endpoint desta
Spec lê AnalysisSkill — ela só é escrita.

Analysis.session_id (SPEC 0009): isola análises por sessão anônima
(UUID gerado no frontend, enviado via header X-Session-Id). Não identifica
uma pessoa — é só um identificador de navegador/origem, sem autenticação
real. AnalysisSkill não tem session_id próprio (evita desnormalização
desnecessária) — o isolamento nela é sempre feito via JOIN com Analysis.

Analysis.semantic_score/hybrid_score/semantic_matches (SPEC 0011): todas
nullable, sem server_default — ficam NULL enquanto ENABLE_SEMANTIC_MATCHING
estiver desligada (padrão) ou quando o serviço de embeddings falhar. Nunca
armazenam vetores de embedding — semantic_matches guarda só nomes de skills
e um float de similaridade (ver app/repositories/analysis_repository.py).

Analysis.llm_summary/llm_improvement_plan/llm_study_suggestions/
llm_resume_tips (SPEC 0014): todas nullable, sem server_default — ficam
NULL enquanto ENABLE_LLM_FEEDBACK estiver desligada (padrão) ou quando o
LLM falhar/timeoutar/responder inválido. Nunca armazenam o prompt completo
nem a resposta bruta do modelo — apenas os campos já validados (ver
app/services/llm_feedback_service.py).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_TIMESTAMP = DateTime(timezone=True)


class ResumeDocument(Base):
    """Metadados de um currículo enviado — nunca o PDF ou o texto em si."""

    __tablename__ = "resume_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pdf_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    resume_text_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resume_text_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(_TIMESTAMP, default=_utcnow)


class JobPosting(Base):
    """Metadados de uma descrição de vaga — nunca o texto completo."""

    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    description_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extracted_skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(_TIMESTAMP, default=_utcnow)


class Analysis(Base):
    """Resultado estruturado de uma análise — espelha o AnalyzeResponse."""

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_documents.id"), nullable=False
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    match_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    insights: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    semantic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hybrid_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semantic_matches: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_improvement_plan: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    llm_study_suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    llm_resume_tips: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TIMESTAMP, default=_utcnow)

    skills: Mapped[list["AnalysisSkill"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class AnalysisSkill(Base):
    """Uma linha por skill (matched/partial/missing/extra) — índice para analytics futuros."""

    __tablename__ = "analysis_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # matched|partial|missing|extra

    analysis: Mapped["Analysis"] = relationship(back_populates="skills")
