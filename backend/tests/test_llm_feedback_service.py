"""
test_llm_feedback_service.py — Testes de app.services.llm_feedback_service (SPEC 0014).

Usa uma função de geração injetada (mock/stub) — nunca depende de um
Ollama real. Cobre: resposta válida, JSON inválido, schema incorreto,
campos extras ignorados, truncamento de listas, e propagação de falha do
provider (LLMUnavailableError e exceção genérica) como fallback (None).
"""

import json

from app.services.llm_feedback_service import MAX_LIST_ITEMS, generate_feedback
from app.services.llm_providers.base import LLMUnavailableError

SAMPLE_RESULT = {
    "score": 67,
    "matched_skills": ["python", "docker"],
    "missing_skills": ["aws"],
    "partial_skills": ["english_advanced"],
    "extra_skills": ["kubernetes"],
    "insights": {"strengths": ["ponto forte"], "weaknesses": ["gap"], "priority_actions": []},
    "recommendations": ["recomendacao de teste"],
}

VALID_LLM_RESPONSE = json.dumps(
    {
        "llm_summary": "Resumo curto do resultado.",
        "llm_improvement_plan": ["passo 1", "passo 2"],
        "llm_study_suggestions": ["estudar aws"],
        "llm_resume_tips": ["destacar docker"],
    }
)


def test_generate_feedback_returns_fields_on_valid_response():
    result = generate_feedback(SAMPLE_RESULT, generate_fn=lambda prompt: VALID_LLM_RESPONSE)

    assert result == {
        "llm_summary": "Resumo curto do resultado.",
        "llm_improvement_plan": ["passo 1", "passo 2"],
        "llm_study_suggestions": ["estudar aws"],
        "llm_resume_tips": ["destacar docker"],
    }


def test_generate_feedback_prompt_never_contains_raw_pdf_or_session_id():
    captured_prompt = {}

    def _capture(prompt):
        captured_prompt["value"] = prompt
        return VALID_LLM_RESPONSE

    generate_feedback(SAMPLE_RESULT, generate_fn=_capture)

    prompt = captured_prompt["value"]
    assert "session_id" not in prompt
    assert "pdf" not in prompt.lower()
    assert "%PDF" not in prompt


def test_generate_feedback_returns_none_on_invalid_json():
    result = generate_feedback(SAMPLE_RESULT, generate_fn=lambda prompt: "isso nao e json valido")

    assert result is None


def test_generate_feedback_returns_none_when_required_field_missing():
    incomplete_response = json.dumps({"llm_summary": "resumo sem os outros campos"})

    result = generate_feedback(SAMPLE_RESULT, generate_fn=lambda prompt: incomplete_response)

    assert result is None


def test_generate_feedback_returns_none_when_field_has_wrong_type():
    wrong_type_response = json.dumps(
        {
            "llm_summary": "resumo",
            "llm_improvement_plan": "deveria ser uma lista, nao uma string",
            "llm_study_suggestions": [],
            "llm_resume_tips": [],
        }
    )

    result = generate_feedback(SAMPLE_RESULT, generate_fn=lambda prompt: wrong_type_response)

    assert result is None


def test_generate_feedback_ignores_extra_fields_in_response():
    response_with_extra_field = json.dumps(
        {
            "llm_summary": "resumo",
            "llm_improvement_plan": [],
            "llm_study_suggestions": [],
            "llm_resume_tips": [],
            "campo_inesperado": "deve ser ignorado, nao invalidar a resposta",
        }
    )

    result = generate_feedback(SAMPLE_RESULT, generate_fn=lambda prompt: response_with_extra_field)

    assert result is not None
    assert "campo_inesperado" not in result


def test_generate_feedback_truncates_lists_to_max_items():
    long_list = [f"item {i}" for i in range(10)]
    response_with_long_lists = json.dumps(
        {
            "llm_summary": "resumo",
            "llm_improvement_plan": long_list,
            "llm_study_suggestions": long_list,
            "llm_resume_tips": long_list,
        }
    )

    result = generate_feedback(SAMPLE_RESULT, generate_fn=lambda prompt: response_with_long_lists)

    assert len(result["llm_improvement_plan"]) == MAX_LIST_ITEMS
    assert len(result["llm_study_suggestions"]) == MAX_LIST_ITEMS
    assert len(result["llm_resume_tips"]) == MAX_LIST_ITEMS


def test_generate_feedback_returns_none_when_provider_raises_llm_unavailable():
    def _raise(prompt):
        raise LLMUnavailableError("simulado: Ollama indisponível")

    result = generate_feedback(SAMPLE_RESULT, generate_fn=_raise)

    assert result is None


def test_generate_feedback_returns_none_on_unexpected_provider_exception():
    def _raise(prompt):
        raise RuntimeError("erro inesperado simulado")

    result = generate_feedback(SAMPLE_RESULT, generate_fn=_raise)

    assert result is None


def test_generate_feedback_returns_none_when_no_provider_configured(monkeypatch):
    import app.services.llm_feedback_service as service_module

    monkeypatch.setattr(service_module, "LLM_PROVIDER", "provider_inexistente")

    result = generate_feedback(SAMPLE_RESULT)

    assert result is None
