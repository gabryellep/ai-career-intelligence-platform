"""
analysis_repository.py — Persistência e leitura de análises (SPEC 0004/0005).

save_analysis é chamado exclusivamente por app/services/analysis_service.py
— nunca pela rota HTTP nem pelo motor determinístico. list_analyses e
get_analysis_by_id (SPEC 0005) são chamados pelas rotas de leitura do
histórico (app/api/v1/routes/analyses.py).

Regra de privacidade: nenhuma função deste módulo recebe, grava ou lê de
volta o PDF bruto, o texto completo do currículo, ou o texto completo da
descrição da vaga. save_analysis recebe pdf_bytes/job_description apenas
para calcular hashes (SHA-256); as funções de leitura nunca selecionam
colunas de hash — apenas score, skills, insights, recomendações e datas.

Isolamento por sessão (SPEC 0009): save_analysis grava session_id; as
funções de leitura filtram por session_id. get_analysis_by_id retorna
None (nunca lança/expõe) para uma análise que existe mas pertence a outra
sessão — a rota converte isso em 404, nunca 403, para não revelar a
existência da análise a quem não tem acesso a ela.

Campos semânticos (SPEC 0011): save_analysis grava semantic_score,
hybrid_score e semantic_matches apenas se presentes em `result` — ausentes
quando ENABLE_SEMANTIC_MATCHING está desligada ou o serviço de embeddings
falha, resultando em NULL nas colunas (todas nullable, ver
app/db/models.py). Nunca grava vetores de embedding.

Campos de feedback via LLM (SPEC 0014): save_analysis grava llm_summary,
llm_improvement_plan, llm_study_suggestions e llm_resume_tips apenas se
presentes em `result` — ausentes quando ENABLE_LLM_FEEDBACK está desligada
ou o LLM falha/timeouta/responde inválido, resultando em NULL nas colunas.
Nunca grava o prompt completo nem a resposta bruta do modelo.
"""

import hashlib
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.db.models import Analysis, AnalysisSkill, JobPosting, ResumeDocument

_SKILL_STATUSES = ("matched", "partial", "missing", "extra")


def save_analysis(
    db: Session,
    pdf_bytes: bytes,
    job_description: str,
    resume_text_sha256: str | None,
    resume_text_length: int,
    result: dict,
    session_id: UUID,
) -> Analysis:
    """
    Persiste ResumeDocument, JobPosting, Analysis e AnalysisSkill em uma
    única transação. Faz commit ao final; em caso de exceção, faz rollback
    e relança para o chamador decidir como tratar (ver AnalysisService).
    """
    try:
        match_details = result.get("match_details", {})

        resume_document = ResumeDocument(
            pdf_sha256=hashlib.sha256(pdf_bytes).hexdigest(),
            resume_text_sha256=resume_text_sha256,
            resume_text_length=resume_text_length,
        )

        # Skills exigidas pela vaga = união de matched + partial + missing
        # (skills que a vaga pede, independentemente de o currículo atender).
        job_required_skills = sorted(
            set(match_details.get("matched", []))
            | set(match_details.get("partial", []))
            | set(match_details.get("missing", []))
        )
        job_posting = JobPosting(
            description_sha256=hashlib.sha256(job_description.encode("utf-8")).hexdigest(),
            description_length=len(job_description),
            extracted_skills=job_required_skills,
        )

        db.add(resume_document)
        db.add(job_posting)
        db.flush()  # garante resume_document.id / job_posting.id antes do FK

        analysis = Analysis(
            resume_document_id=resume_document.id,
            job_posting_id=job_posting.id,
            session_id=session_id,
            score=result.get("score", 0),
            match_details=match_details,
            insights=result.get("insights", {}),
            recommendations=result.get("recommendations", []),
            semantic_score=result.get("semantic_score"),
            hybrid_score=result.get("hybrid_score"),
            semantic_matches=result.get("semantic_matches"),
            llm_summary=result.get("llm_summary"),
            llm_improvement_plan=result.get("llm_improvement_plan"),
            llm_study_suggestions=result.get("llm_study_suggestions"),
            llm_resume_tips=result.get("llm_resume_tips"),
        )
        db.add(analysis)
        db.flush()

        for status in _SKILL_STATUSES:
            for skill_name in match_details.get(status, []):
                db.add(AnalysisSkill(analysis_id=analysis.id, skill_name=skill_name, status=status))

        db.commit()
        db.refresh(analysis)
        return analysis

    except Exception:
        db.rollback()
        raise


def list_analyses(
    db: Session,
    session_id: UUID,
    limit: int = 20,
    offset: int = 0,
    min_score: int | None = None,
    skill_status: str | None = None,
    skill_name: str | None = None,
) -> tuple[list[Analysis], int]:
    """
    Lista análises da sessão informada (mais recentes primeiro), com
    paginação e filtros opcionais. Retorna (itens da página, contagem
    total sem paginação) — ambos já restritos a session_id.

    Filtros de skill usam EXISTS contra AnalysisSkill para evitar duplicar
    linhas de Analysis quando uma análise tem múltiplas skills que batem
    com o filtro (join comum causaria 1 linha por skill correspondente).

    Ordenação (SPEC 0010): created_at DESC, id DESC. O desempate por id
    existe porque duas análises criadas em sucessão rápida podem receber
    o mesmo created_at até o microssegundo (confirmado empiricamente na
    verificação da SPEC 0009), o que tornava "mais recente primeiro"
    não-determinístico em empates — id (chave primária, já indexada) só
    serve para estabilizar a ordem, sem relação cronológica própria.
    """
    query = select(Analysis).where(Analysis.session_id == session_id)

    if min_score is not None:
        query = query.where(Analysis.score >= min_score)

    if skill_status is not None or skill_name is not None:
        skill_conditions = [AnalysisSkill.analysis_id == Analysis.id]
        if skill_status is not None:
            skill_conditions.append(AnalysisSkill.status == skill_status)
        if skill_name is not None:
            skill_conditions.append(AnalysisSkill.skill_name == skill_name)
        query = query.where(exists().where(*skill_conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    paginated_query = query.order_by(Analysis.created_at.desc(), Analysis.id.desc()).limit(limit).offset(offset)
    items = list(db.execute(paginated_query).scalars().all())

    return items, total


def get_analysis_by_id(db: Session, analysis_id: UUID, session_id: UUID) -> Analysis | None:
    """
    Retorna uma análise pelo id, restrita à sessão informada. Retorna None
    tanto se o id não existir quanto se existir mas pertencer a outra
    sessão — a rota trata os dois casos da mesma forma (404), nunca
    revelando a existência de análises de outras sessões.
    """
    query = select(Analysis).where(Analysis.id == analysis_id, Analysis.session_id == session_id)
    return db.execute(query).scalar_one_or_none()
