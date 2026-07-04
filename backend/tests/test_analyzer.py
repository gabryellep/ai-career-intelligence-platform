"""
test_analyzer.py — Testes de integração do módulo analyzer.py.

Testa a função analyze que orquestra todos os módulos:
parser → skills → scorer → recommender.

Os PDFs são criados programaticamente com PyMuPDF para não depender
de arquivos externos.
"""

import fitz  # PyMuPDF

import app.engines.deterministic.analyzer as analyzer_module
import app.engines.semantic.hybrid as hybrid_module
from app.engines.deterministic.analyzer import analyze

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_pdf_with_text(text: str) -> bytes:
    """Cria um PDF simples em memória com o texto fornecido."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 100), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def create_empty_pdf() -> bytes:
    """Cria um PDF válido sem texto (página em branco)."""
    document = fitz.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# Testes: estrutura do retorno
# ---------------------------------------------------------------------------


def test_analyze_returns_required_keys():
    """O retorno deve conter as 4 chaves obrigatórias."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos desenvolvedor Python com experiência em FastAPI e AWS."

    result = analyze(pdf_bytes, job)

    assert "score" in result
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert "recommendations" in result


def test_analyze_return_types():
    """Os tipos de retorno devem ser int, list, list, list."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos Python, FastAPI e AWS."

    result = analyze(pdf_bytes, job)

    assert isinstance(result["score"], int)
    assert isinstance(result["matched_skills"], list)
    assert isinstance(result["missing_skills"], list)
    assert isinstance(result["recommendations"], list)


def test_analyze_score_in_valid_range():
    """O score deve estar sempre entre 0 e 100."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos Python, FastAPI e AWS."

    result = analyze(pdf_bytes, job)

    assert 0 <= result["score"] <= 100


# ---------------------------------------------------------------------------
# Testes: PDF com texto
# ---------------------------------------------------------------------------


def test_analyze_with_matching_skills():
    """PDF com skills da vaga deve retornar matched_skills não vazio."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos desenvolvedor com Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    assert len(result["matched_skills"]) > 0
    assert "python" in result["matched_skills"]
    assert "fastapi" in result["matched_skills"]
    assert "docker" in result["matched_skills"]


def test_analyze_missing_skills_are_correct():
    """Skills da vaga ausentes no currículo devem aparecer em missing_skills."""
    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python, FastAPI e AWS."

    result = analyze(pdf_bytes, job)

    assert "aws" in result["missing_skills"]
    assert "python" not in result["missing_skills"]
    assert "fastapi" not in result["missing_skills"]


def test_analyze_recommendations_not_empty_when_missing_skills():
    """Quando há skills faltantes, recommendations não deve ser vazio."""
    pdf_bytes = create_pdf_with_text("Python")
    job = "Buscamos Python, FastAPI, Docker e AWS."

    result = analyze(pdf_bytes, job)

    assert len(result["recommendations"]) > 0


# ---------------------------------------------------------------------------
# Testes: PDF sem texto
# ---------------------------------------------------------------------------


def test_analyze_with_empty_pdf_returns_valid_structure():
    """PDF sem texto deve retornar estrutura válida com listas vazias ou padrão."""
    pdf_bytes = create_empty_pdf()
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    # Estrutura deve estar presente
    assert "score" in result
    assert isinstance(result["matched_skills"], list)
    assert isinstance(result["missing_skills"], list)
    assert isinstance(result["recommendations"], list)


def test_analyze_with_empty_pdf_score_is_zero():
    """PDF sem texto deve retornar score 0 (sem skills no currículo)."""
    pdf_bytes = create_empty_pdf()
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    assert result["score"] == 0


def test_analyze_with_empty_pdf_matched_skills_is_empty_list():
    """PDF sem texto deve retornar matched_skills como lista vazia."""
    pdf_bytes = create_empty_pdf()
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    assert result["matched_skills"] == []


def test_analyze_with_empty_pdf_missing_skills_is_list():
    """PDF sem texto deve retornar missing_skills como lista (com as skills da vaga)."""
    pdf_bytes = create_empty_pdf()
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    assert isinstance(result["missing_skills"], list)
    assert len(result["missing_skills"]) > 0


def test_analyze_with_invalid_bytes_returns_valid_structure():
    """Bytes inválidos devem retornar estrutura válida sem lançar exceção."""
    result = analyze(b"nao e um pdf", "Buscamos Python e Docker.")

    assert isinstance(result["score"], int)
    assert isinstance(result["matched_skills"], list)
    assert isinstance(result["missing_skills"], list)
    assert isinstance(result["recommendations"], list)


# ---------------------------------------------------------------------------
# Testes: campo de debug
# ---------------------------------------------------------------------------


def test_analyze_debug_false_no_preview():
    """Sem debug=True, o campo resume_text_preview não deve estar presente."""
    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job, debug=False)

    assert "resume_text_preview" not in result


def test_analyze_debug_true_includes_preview():
    """Com debug=True, o campo resume_text_preview deve estar presente."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job, debug=True)

    assert "resume_text_preview" in result
    assert isinstance(result["resume_text_preview"], str)


def test_analyze_debug_preview_max_500_chars():
    """O resume_text_preview deve ter no máximo 500 caracteres."""
    long_text = "Python " * 200  # texto longo
    pdf_bytes = create_pdf_with_text(long_text)
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job, debug=True)

    assert len(result["resume_text_preview"]) <= 500


# ---------------------------------------------------------------------------
# Testes dos novos campos (Bloco 3 — integração com matcher)
# ---------------------------------------------------------------------------


def test_analyze_returns_partial_skills_field():
    """O retorno deve conter o campo 'partial_skills'."""
    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    assert "partial_skills" in result
    assert isinstance(result["partial_skills"], list)


def test_analyze_returns_extra_skills_field():
    """O retorno deve conter o campo 'extra_skills'."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker AWS")
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job)

    assert "extra_skills" in result
    assert isinstance(result["extra_skills"], list)


def test_analyze_returns_match_details_field():
    """O retorno deve conter o campo 'match_details' com as chaves do matcher."""
    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python e Docker."

    result = analyze(pdf_bytes, job)

    assert "match_details" in result
    assert "matched" in result["match_details"]
    assert "partial" in result["match_details"]
    assert "missing" in result["match_details"]
    assert "extra" in result["match_details"]


def test_analyze_english_intermediate_partial_for_advanced():
    """
    Currículo com english_intermediate e python.
    Vaga pede english_advanced, python e docker.
    Esperado:
        - python em matched_skills
        - english_advanced em partial_skills
        - docker em missing_skills
        - score ponderado coerente (menor que 100)
    """
    # Cria PDF com texto que skills.py detecta como english_intermediate e python
    pdf_bytes = create_pdf_with_text("Python inglês intermediário B2")
    job = "Buscamos Python com inglês avançado C1 e Docker."

    result = analyze(pdf_bytes, job)

    # python deve estar em matched
    assert "python" in result["matched_skills"]

    # docker deve estar em missing
    assert "docker" in result["missing_skills"]

    # deve haver pelo menos uma skill parcial (inglês)
    assert len(result["partial_skills"]) > 0

    # score deve ser menor que 100 (não atende tudo completamente)
    assert result["score"] < 100

    # score deve ser maior que 0 (python foi matched)
    assert result["score"] > 0


def test_analyze_extra_skills_not_in_job():
    """Skills do currículo além do exigido devem aparecer em extra_skills."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker AWS Kubernetes")
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job)

    # python deve estar em matched
    assert "python" in result["matched_skills"]

    # skills extras devem existir
    assert len(result["extra_skills"]) > 0

    # nenhuma skill extra deve estar em matched ou missing
    for skill in result["extra_skills"]:
        assert skill not in result["matched_skills"]
        assert skill not in result["missing_skills"]


# ---------------------------------------------------------------------------
# Testes: matching semântico opcional (SPEC 0011)
# ---------------------------------------------------------------------------


def test_analyze_uses_contextual_job_requirements():
    """Skills desejaveis pesam menos e mencoes negadas nao viram gap."""
    pdf_bytes = create_pdf_with_text("Python")
    job = "Required: Python. Docker is a plus. No experience with AWS required. Senior role."

    result = analyze(pdf_bytes, job)

    assert "python" in result["matched_skills"]
    assert "docker" in result["missing_skills"]
    assert "aws" not in result["missing_skills"]
    assert result["score"] == 74
    assert result["match_details"]["job_context"]["seniority"] == "senior"


def test_analyze_includes_career_improvement_plan_for_real_gaps():
    pdf_bytes = create_pdf_with_text("Python")
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    plan = result["career_improvement_plan"]
    plan_skills = [item["skill"] for item in plan["items"]]
    assert plan_skills == result["missing_skills"]
    assert "python" not in plan_skills
    assert "somente depois" in plan["items"][0]["resume_guidance"]


def test_analyze_omits_career_improvement_plan_without_gaps():
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos Python, FastAPI e Docker."

    result = analyze(pdf_bytes, job)

    assert result["missing_skills"] == []
    assert result["partial_skills"] == []
    assert "career_improvement_plan" not in result


def test_analyze_with_flag_disabled_omits_semantic_fields(monkeypatch):
    """Com ENABLE_SEMANTIC_MATCHING desligada (padrão), os 3 campos semânticos não aparecem."""
    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", False)

    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python, FastAPI e AWS."

    result = analyze(pdf_bytes, job)

    assert "semantic_score" not in result
    assert "hybrid_score" not in result
    assert "semantic_matches" not in result


def test_analyze_semantic_enrichment_never_changes_deterministic_fields(monkeypatch):
    """
    Com a flag ligada e o serviço semântico mockado com sucesso, score,
    matched_skills, missing_skills, partial_skills, extra_skills e
    match_details devem permanecer idênticos ao resultado sem a flag —
    prova de que o motor determinístico não foi alterado por esta Spec.
    """
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")
    job = "Buscamos Python, FastAPI e AWS."

    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", False)
    baseline = analyze(pdf_bytes, job)

    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(
        hybrid_module,
        "enrich_with_semantic_matching",
        lambda skill_match, score: {"semantic_score": 99, "hybrid_score": 95, "semantic_matches": []},
    )
    enriched = analyze(pdf_bytes, job)

    assert enriched["score"] == baseline["score"]
    assert enriched["matched_skills"] == baseline["matched_skills"]
    assert enriched["missing_skills"] == baseline["missing_skills"]
    assert enriched["partial_skills"] == baseline["partial_skills"]
    assert enriched["extra_skills"] == baseline["extra_skills"]
    assert enriched["match_details"] == baseline["match_details"]

    assert enriched["semantic_score"] == 99
    assert enriched["hybrid_score"] == 95
    assert enriched["semantic_matches"] == []


def test_analyze_semantic_failure_falls_back_silently(monkeypatch):
    """
    Se o serviço semântico lançar uma exceção (dependência ausente, erro de
    modelo etc.), analyze() não deve propagar — apenas omite os 3 campos,
    mantendo o resultado determinístico intacto.
    """
    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", True)

    def _raise(skill_match, score):
        raise RuntimeError("falha simulada do serviço de embeddings")

    monkeypatch.setattr(hybrid_module, "enrich_with_semantic_matching", _raise)

    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job)

    assert "semantic_score" not in result
    assert "hybrid_score" not in result
    assert "semantic_matches" not in result
    assert isinstance(result["score"], int)
    assert isinstance(result["matched_skills"], list)


def test_analyze_semantic_returns_none_falls_back_silently(monkeypatch):
    """Se enrich_with_semantic_matching retornar None (fallback interno), os campos ficam ausentes."""
    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(hybrid_module, "enrich_with_semantic_matching", lambda skill_match, score: None)

    pdf_bytes = create_pdf_with_text("Python FastAPI")
    job = "Buscamos Python."

    result = analyze(pdf_bytes, job)

    assert "semantic_score" not in result
    assert "hybrid_score" not in result
    assert "semantic_matches" not in result
