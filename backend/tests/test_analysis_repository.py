"""
test_analysis_repository.py — Testes de integração do AnalysisRepository (SPEC 0004).

Requerem um PostgreSQL acessível via DATABASE_URL (app/core/config.py).
Se a conexão falhar, os testes deste módulo são pulados — permite rodar a
suíte localmente sem Docker/Postgres rodando. No CI, um serviço postgres
(ver .github/workflows/ci.yml) garante que esses testes rodem de verdade.
"""

import uuid

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL
from app.db.base import Base
from app.db.models import Analysis, AnalysisSkill, JobPosting, ResumeDocument
from app.repositories.analysis_repository import save_analysis
from main import app as fastapi_app

SESSION_ID = uuid.uuid4()


def _database_available() -> bool:
    try:
        probe_engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with probe_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        probe_engine.dispose()
        return True
    except OperationalError:
        return False


pytestmark = pytest.mark.skipif(
    not _database_available(),
    reason="PostgreSQL não disponível em DATABASE_URL — pulando testes de integração de banco.",
)


@pytest.fixture()
def db_session():
    """
    Garante um schema limpo antes de cada teste (drop_all + create_all),
    entrega uma sessão e limpa ao final.

    O drop_all() no setup (além do teardown) é necessário porque dados de
    execuções anteriores fora da suíte (ex.: chamadas manuais a POST /analyze
    contra o mesmo DATABASE_URL) podem deixar linhas residuais nas tabelas —
    sem isso, contagens como "1 registro criado" ficam não-determinísticas.
    """
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


SAMPLE_RESULT = {
    "score": 67,
    "match_details": {
        "matched": ["python", "docker"],
        "partial": ["english_advanced"],
        "missing": ["aws"],
        "extra": ["kubernetes"],
    },
    "insights": {"strengths": ["ponto forte"], "weaknesses": [], "priority_actions": []},
    "recommendations": ["recomendacao de teste"],
}


def test_save_analysis_creates_all_records(db_session):
    """save_analysis deve criar 1 ResumeDocument, 1 JobPosting, 1 Analysis e N AnalysisSkill."""
    analysis = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 conteudo de teste",
        job_description="Buscamos Python, Docker, AWS.",
        resume_text_sha256="abc123",
        resume_text_length=42,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )

    assert db_session.query(ResumeDocument).count() == 1
    assert db_session.query(JobPosting).count() == 1
    assert db_session.query(Analysis).count() == 1
    # matched(2) + partial(1) + missing(1) + extra(1) = 5 linhas
    assert db_session.query(AnalysisSkill).count() == 5
    assert analysis.score == 67


def test_save_analysis_never_stores_raw_content(db_session):
    """Nenhuma tabela deve conter o PDF bruto ou o texto completo enviado."""
    pdf_bytes = b"%PDF-1.4 dados sensiveis do curriculo com nome e telefone"
    job_description = "descricao completa e potencialmente sensivel da vaga"

    save_analysis(
        db_session,
        pdf_bytes=pdf_bytes,
        job_description=job_description,
        resume_text_sha256="deadbeef",
        resume_text_length=10,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )

    resume_doc = db_session.query(ResumeDocument).one()
    job_posting = db_session.query(JobPosting).one()

    assert len(resume_doc.pdf_sha256) == 64  # hex digest do sha256, nunca o conteúdo
    assert len(job_posting.description_sha256) == 64
    assert pdf_bytes.decode(errors="ignore") not in resume_doc.pdf_sha256
    assert job_description not in job_posting.description_sha256


def test_save_analysis_extracted_skills_reflects_job_requirements(db_session):
    """JobPosting.extracted_skills deve ser a união de matched+partial+missing."""
    save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4",
        job_description="vaga de teste",
        resume_text_sha256=None,
        resume_text_length=0,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )
    job_posting = db_session.query(JobPosting).one()
    assert set(job_posting.extracted_skills) == {"python", "docker", "english_advanced", "aws"}


def test_save_analysis_persists_semantic_fields_when_present(db_session):
    """
    Quando result inclui semantic_score/hybrid_score/semantic_matches (SPEC
    0011 — ENABLE_SEMANTIC_MATCHING ligada e serviço semântico bem-sucedido),
    save_analysis deve gravá-los.
    """
    result_with_semantic = dict(SAMPLE_RESULT)
    result_with_semantic["semantic_score"] = 80
    result_with_semantic["hybrid_score"] = 75
    result_with_semantic["semantic_matches"] = [
        {"job_skill": "machine learning", "matched_resume_skill": "ml", "similarity": 0.85}
    ]

    analysis = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 semantico",
        job_description="vaga com bastante texto para passar da validacao",
        resume_text_sha256=None,
        resume_text_length=0,
        result=result_with_semantic,
        session_id=SESSION_ID,
    )

    assert analysis.semantic_score == 80
    assert analysis.hybrid_score == 75
    assert analysis.semantic_matches == [
        {"job_skill": "machine learning", "matched_resume_skill": "ml", "similarity": 0.85}
    ]


def test_save_analysis_semantic_fields_null_when_absent(db_session):
    """Quando result não inclui campos semânticos (flag desligada, o caso padrão), ficam NULL."""
    analysis = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 sem semantico",
        job_description="vaga com bastante texto para passar da validacao",
        resume_text_sha256=None,
        resume_text_length=0,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )

    assert analysis.semantic_score is None
    assert analysis.hybrid_score is None
    assert analysis.semantic_matches is None


def test_save_analysis_persists_llm_feedback_fields_when_present(db_session):
    """Quando result inclui os campos llm_* (SPEC 0014), save_analysis deve gravá-los."""
    result_with_llm = dict(SAMPLE_RESULT)
    result_with_llm["llm_summary"] = "resumo gerado pelo LLM"
    result_with_llm["llm_improvement_plan"] = ["passo 1", "passo 2"]
    result_with_llm["llm_study_suggestions"] = ["estudar aws"]
    result_with_llm["llm_resume_tips"] = ["destacar docker"]

    analysis = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 com llm",
        job_description="vaga com bastante texto para passar da validacao",
        resume_text_sha256=None,
        resume_text_length=0,
        result=result_with_llm,
        session_id=SESSION_ID,
    )

    assert analysis.llm_summary == "resumo gerado pelo LLM"
    assert analysis.llm_improvement_plan == ["passo 1", "passo 2"]
    assert analysis.llm_study_suggestions == ["estudar aws"]
    assert analysis.llm_resume_tips == ["destacar docker"]


def test_save_analysis_llm_feedback_fields_null_when_absent(db_session):
    """Quando result não inclui campos llm_* (flag desligada, o caso padrão), ficam NULL."""
    analysis = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 sem llm",
        job_description="vaga com bastante texto para passar da validacao",
        resume_text_sha256=None,
        resume_text_length=0,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )

    assert analysis.llm_summary is None
    assert analysis.llm_improvement_plan is None
    assert analysis.llm_study_suggestions is None
    assert analysis.llm_resume_tips is None


def test_list_analyses_orders_deterministically_on_created_at_ties(db_session):
    """
    Duas análises com created_at idêntico (forçado via UPDATE direto,
    simulando a condição de corrida real observada na verificação da
    SPEC 0009 — duas gravações no mesmo microssegundo) devem ser
    ordenadas de forma estável e determinística entre chamadas
    repetidas, com id DESC como critério de desempate (SPEC 0010).
    """
    from app.repositories.analysis_repository import list_analyses

    analysis_a = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 a",
        job_description="vaga a com bastante texto para passar da validacao",
        resume_text_sha256=None,
        resume_text_length=0,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )
    analysis_b = save_analysis(
        db_session,
        pdf_bytes=b"%PDF-1.4 b",
        job_description="vaga b com bastante texto para passar da validacao",
        resume_text_sha256=None,
        resume_text_length=0,
        result=SAMPLE_RESULT,
        session_id=SESSION_ID,
    )

    tied_timestamp = analysis_a.created_at
    db_session.execute(
        text("UPDATE analyses SET created_at = :ts WHERE id IN (:a, :b)"),
        {"ts": tied_timestamp, "a": analysis_a.id, "b": analysis_b.id},
    )
    db_session.commit()

    items_first_call, _ = list_analyses(db_session, session_id=SESSION_ID)
    items_second_call, _ = list_analyses(db_session, session_id=SESSION_ID)

    ids_first = [item.id for item in items_first_call]
    ids_second = [item.id for item in items_second_call]

    assert ids_first == ids_second  # ordem determinística entre chamadas repetidas

    tied_ids_in_order = [i for i in ids_first if i in (analysis_a.id, analysis_b.id)]
    assert tied_ids_in_order == sorted([analysis_a.id, analysis_b.id], reverse=True)


def test_post_analyze_creates_analysis_row_when_db_available(db_session):
    """Uma chamada bem-sucedida a POST /analyze deve gerar 1 registro em analyses."""
    client = TestClient(fastapi_app)

    before = db_session.query(Analysis).count()

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Python FastAPI Docker")
    pdf_bytes = doc.tobytes()
    doc.close()

    response = client.post(
        "/analyze",
        files={"file": ("cv.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": "Buscamos Python, FastAPI, Docker e AWS com experiencia solida."},
    )
    assert response.status_code == 200

    db_session.expire_all()
    after = db_session.query(Analysis).count()
    assert after == before + 1
