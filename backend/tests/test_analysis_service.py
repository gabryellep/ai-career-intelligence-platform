"""
test_analysis_service.py — Testes de app.services.analysis_service (SPEC 0014).

Cobre a integração do feedback via LLM no ponto de chamada
(run_analysis) — mock/stub apenas, nunca um Ollama real. A persistência
(SPEC 0004) já falha silenciosamente sem banco disponível, então estes
testes não exigem PostgreSQL.
"""

import uuid

import fitz  # PyMuPDF

import app.services.analysis_service as analysis_service_module
from app.services.analysis_service import run_analysis

SESSION_ID = uuid.uuid4()


def create_pdf_with_text(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 100), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def test_run_analysis_with_flag_disabled_omits_llm_fields(monkeypatch):
    monkeypatch.setattr(analysis_service_module, "ENABLE_LLM_FEEDBACK", False)

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    result = run_analysis(pdf_bytes, "Buscamos Python, FastAPI e AWS.", session_id=SESSION_ID)

    assert "llm_summary" not in result
    assert "llm_improvement_plan" not in result
    assert "llm_study_suggestions" not in result
    assert "llm_resume_tips" not in result


def test_run_analysis_with_flag_enabled_and_successful_feedback_adds_fields(monkeypatch):
    monkeypatch.setattr(analysis_service_module, "ENABLE_LLM_FEEDBACK", True)
    monkeypatch.setattr(
        analysis_service_module,
        "generate_feedback",
        lambda result: {
            "llm_summary": "resumo gerado",
            "llm_improvement_plan": ["passo 1"],
            "llm_study_suggestions": ["estudar x"],
            "llm_resume_tips": ["dica 1"],
        },
    )

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    result = run_analysis(pdf_bytes, "Buscamos Python, FastAPI e AWS.", session_id=SESSION_ID)

    assert result["llm_summary"] == "resumo gerado"
    assert result["llm_improvement_plan"] == ["passo 1"]
    assert result["llm_study_suggestions"] == ["estudar x"]
    assert result["llm_resume_tips"] == ["dica 1"]
    # campos determinísticos continuam presentes e não foram alterados
    assert "score" in result
    assert "matched_skills" in result


def test_run_analysis_llm_failure_falls_back_silently(monkeypatch):
    monkeypatch.setattr(analysis_service_module, "ENABLE_LLM_FEEDBACK", True)

    def _raise(result):
        raise RuntimeError("falha simulada do serviço de LLM")

    monkeypatch.setattr(analysis_service_module, "generate_feedback", _raise)

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    result = run_analysis(pdf_bytes, "Buscamos Python, FastAPI e AWS.", session_id=SESSION_ID)

    assert "llm_summary" not in result
    assert "llm_improvement_plan" not in result
    assert "llm_study_suggestions" not in result
    assert "llm_resume_tips" not in result
    assert isinstance(result["score"], int)


def test_run_analysis_llm_returns_none_falls_back_silently(monkeypatch):
    monkeypatch.setattr(analysis_service_module, "ENABLE_LLM_FEEDBACK", True)
    monkeypatch.setattr(analysis_service_module, "generate_feedback", lambda result: None)

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    result = run_analysis(pdf_bytes, "Buscamos Python, FastAPI e AWS.", session_id=SESSION_ID)

    assert "llm_summary" not in result
    assert "llm_improvement_plan" not in result
    assert "llm_study_suggestions" not in result
    assert "llm_resume_tips" not in result
