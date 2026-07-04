"""
test_routes.py — Testes de integração das rotas da API.

Testa as rotas GET /health e POST /analyze usando TestClient do FastAPI.
Os PDFs são criados programaticamente com PyMuPDF.
"""

import fitz  # PyMuPDF
from fastapi.testclient import TestClient

import app.engines.deterministic.analyzer as analyzer_module
from main import app

client = TestClient(app)


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
    """Cria um PDF válido sem texto."""
    document = fitz.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


# Descrição de vaga válida (≥ 50 caracteres)
VALID_JOB = (
    "Buscamos desenvolvedor Python com experiência em FastAPI, Docker e AWS. "
    "Conhecimento em machine learning é um diferencial."
)


# ---------------------------------------------------------------------------
# Testes: GET /health
# ---------------------------------------------------------------------------


def test_health_check_returns_200():
    """GET /health deve retornar HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_returns_status_ok():
    """GET /health deve retornar {"status": "ok"}."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Testes: POST /analyze — casos de sucesso
# ---------------------------------------------------------------------------


def test_analyze_with_valid_pdf_returns_200():
    """POST /analyze com PDF válido deve retornar HTTP 200."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker machine learning")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 200


def test_analyze_response_has_required_fields():
    """POST /analyze deve retornar JSON com as 4 chaves obrigatórias."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "score" in data
    assert "matched_skills" in data
    assert "missing_skills" in data
    assert "recommendations" in data


def test_analyze_score_in_valid_range():
    """O score retornado deve estar entre 0 e 100."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert 0 <= data["score"] <= 100


# ---------------------------------------------------------------------------
# Testes: POST /analyze — validações (erros esperados)
# ---------------------------------------------------------------------------


def test_analyze_with_non_pdf_file_returns_422():
    """Arquivo não-PDF deve retornar HTTP 422."""
    txt_content = b"Isso nao e um PDF"

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.txt", txt_content, "text/plain")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 422


def test_analyze_with_non_pdf_returns_descriptive_message():
    """Arquivo não-PDF deve retornar mensagem de erro descritiva."""
    response = client.post(
        "/analyze",
        files={"file": ("curriculo.txt", b"texto", "text/plain")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) > 0


def test_analyze_with_short_job_description_returns_422():
    """Descrição da vaga com menos de 50 caracteres deve retornar HTTP 422."""
    pdf_bytes = create_pdf_with_text("Python")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": "Python"},  # menos de 50 chars
    )

    assert response.status_code == 422


def test_analyze_with_short_job_description_returns_correct_message():
    """Descrição curta deve retornar a mensagem correta."""
    pdf_bytes = create_pdf_with_text("Python")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": "Curto"},
    )

    data = response.json()
    assert "10 caracteres" in data["detail"]


def test_analyze_with_long_job_description_returns_422():
    """Descrição da vaga com mais de 10.000 caracteres deve retornar HTTP 422."""
    pdf_bytes = create_pdf_with_text("Python")
    long_description = "a" * 10_001

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": long_description},
    )

    assert response.status_code == 422


def test_analyze_with_oversized_file_returns_413():
    """Arquivo maior que 5 MB deve retornar HTTP 413."""
    # Cria conteúdo com mais de 5 MB
    oversized_content = b"%PDF-1.4" + b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/analyze",
        files={"file": ("grande.pdf", oversized_content, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 413


def test_analyze_with_oversized_file_returns_correct_message():
    """Arquivo > 5 MB deve retornar a mensagem correta."""
    oversized_content = b"%PDF-1.4" + b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/analyze",
        files={"file": ("grande.pdf", oversized_content, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "5 MB" in data["detail"]


# ---------------------------------------------------------------------------
# Testes: POST /analyze — segurança de upload (SPEC 0008)
# ---------------------------------------------------------------------------


def test_analyze_with_empty_file_returns_422():
    """Arquivo vazio (0 bytes) deve retornar HTTP 422."""
    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", b"", "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 422


def test_analyze_with_empty_file_returns_descriptive_message():
    """Arquivo vazio deve retornar mensagem descritiva, sem conteúdo do upload."""
    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", b"", "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "vazio" in data["detail"].lower()


def test_analyze_with_fake_pdf_content_returns_422():
    """Extensão/MIME de PDF mas conteúdo sem magic bytes deve retornar HTTP 422."""
    fake_content = b"MZ" + b"conteudo binario qualquer disfarcado de pdf"

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", fake_content, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 422


def test_analyze_with_fake_pdf_content_returns_descriptive_message():
    """Conteúdo sem magic bytes de PDF deve retornar mensagem descritiva."""
    fake_content = b"MZ" + b"conteudo binario qualquer disfarcado de pdf"

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", fake_content, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "detail" in data
    assert fake_content.decode(errors="ignore") not in data["detail"]


def test_analyze_with_wrong_extension_returns_422():
    """Filename com extensão diferente de .pdf deve retornar HTTP 422."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.exe", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 422


def test_analyze_without_file_returns_422():
    """Ausência do campo file deve retornar HTTP 422 (validação automática do FastAPI)."""
    response = client.post(
        "/analyze",
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 422


def test_analyze_error_responses_never_contain_job_description_content():
    """Nenhuma resposta de erro deve ecoar o conteúdo da descrição da vaga enviada."""
    marker = "MARCADOR_UNICO_DA_DESCRICAO_DA_VAGA_DE_TESTE"

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.txt", b"nao e pdf", "text/plain")},
        data={"job_description": marker * 3},
    )

    assert marker not in response.text


# ---------------------------------------------------------------------------
# Testes: persistência (SPEC 0004) — resiliência e ausência de vazamento
# ---------------------------------------------------------------------------


def test_analyze_returns_200_even_if_persistence_fails(monkeypatch):
    """POST /analyze deve continuar retornando 200 mesmo se a persistência falhar."""

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated db failure")

    monkeypatch.setattr("app.services.analysis_service.save_analysis", _boom)

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 200
    assert "score" in response.json()


def test_analyze_response_never_exposes_internal_persistence_keys():
    """A resposta HTTP não deve conter as chaves internas de persistência do motor."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "_resume_text_sha256" not in data
    assert "_resume_text_length" not in data


# ---------------------------------------------------------------------------
# Testes: sessão anônima (SPEC 0009) — X-Session-Id é opcional em /analyze
# ---------------------------------------------------------------------------


def test_analyze_without_session_header_still_returns_200():
    """POST /analyze sem X-Session-Id deve continuar funcionando (UUID gerado automaticamente)."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 200
    assert "score" in response.json()


def test_analyze_with_malformed_session_header_still_returns_200():
    """POST /analyze com X-Session-Id malformado deve gerar um UUID novo, sem quebrar a análise."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
        headers={"X-Session-Id": "isso-nao-e-um-uuid"},
    )

    assert response.status_code == 200
    assert "score" in response.json()


def test_analyze_with_valid_session_header_returns_200():
    """POST /analyze com X-Session-Id válido deve funcionar normalmente."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
        headers={"X-Session-Id": "11111111-1111-1111-1111-111111111111"},
    )

    assert response.status_code == 200
    assert "score" in response.json()


# ---------------------------------------------------------------------------
# Testes: contrato de resposta com matching semântico desligado (SPEC 0011)
# ---------------------------------------------------------------------------


def test_analyze_response_omits_semantic_fields_when_flag_disabled(monkeypatch):
    """
    Com ENABLE_SEMANTIC_MATCHING desligada, a resposta HTTP de POST /analyze
    não deve conter semantic_score, hybrid_score nem semantic_matches — o
    contrato precisa ficar byte-a-byte idêntico ao existente antes da SPEC
    0011 (response_model_exclude_none=True, ver app/api/v1/routes/analyze.py).

    A flag é forçada via monkeypatch (em vez de confiar apenas no padrão de
    app/core/config.py) para que este teste continue correto mesmo que
    ENABLE_SEMANTIC_MATCHING esteja true no ambiente (ex.: verificação manual
    contra Postgres real com a flag ligada para testar persistência).
    """
    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", False)
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "semantic_score" not in data
    assert "hybrid_score" not in data
    assert "semantic_matches" not in data


def test_analyze_response_includes_semantic_fields_when_flag_enabled_and_service_succeeds(monkeypatch):
    """
    Com ENABLE_SEMANTIC_MATCHING ligada e o serviço semântico mockado com
    sucesso, a resposta HTTP passa a incluir os 3 campos aditivos, sem
    alterar score/matched_skills/missing_skills/match_details.
    """
    import app.engines.semantic.hybrid as hybrid_module

    monkeypatch.setattr(analyzer_module, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(
        hybrid_module,
        "enrich_with_semantic_matching",
        lambda skill_match, score: {"semantic_score": 77, "hybrid_score": 70, "semantic_matches": []},
    )

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert data["semantic_score"] == 77
    assert data["hybrid_score"] == 70
    assert data["semantic_matches"] == []
    assert "score" in data
    assert "matched_skills" in data


# ---------------------------------------------------------------------------
# Testes: contrato de resposta com feedback via LLM (SPEC 0014)
# ---------------------------------------------------------------------------


def test_analyze_response_omits_llm_fields_when_flag_disabled(monkeypatch):
    """
    Com ENABLE_LLM_FEEDBACK desligada (forçada via monkeypatch, mesmo padrão
    da SPEC 0011/0012), a resposta HTTP não deve conter llm_summary,
    llm_improvement_plan, llm_study_suggestions nem llm_resume_tips.
    """
    import app.services.analysis_service as analysis_service_module

    monkeypatch.setattr(analysis_service_module, "ENABLE_LLM_FEEDBACK", False)
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "llm_summary" not in data
    assert "llm_improvement_plan" not in data
    assert "llm_study_suggestions" not in data
    assert "llm_resume_tips" not in data


def test_analyze_response_includes_llm_fields_when_flag_enabled_and_service_succeeds(monkeypatch):
    """
    Com ENABLE_LLM_FEEDBACK ligada e o serviço de LLM mockado com sucesso, a
    resposta HTTP passa a incluir os 4 campos aditivos, sem alterar
    score/matched_skills/missing_skills/match_details.
    """
    import app.services.analysis_service as analysis_service_module

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

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert data["llm_summary"] == "resumo gerado"
    assert data["llm_improvement_plan"] == ["passo 1"]
    assert data["llm_study_suggestions"] == ["estudar x"]
    assert data["llm_resume_tips"] == ["dica 1"]
    assert "score" in data
    assert "matched_skills" in data


def test_analyze_response_omits_llm_fields_when_service_fails(monkeypatch):
    """Falha do serviço de LLM (exceção) não deve quebrar /analyze nem incluir campos parciais."""
    import app.services.analysis_service as analysis_service_module

    monkeypatch.setattr(analysis_service_module, "ENABLE_LLM_FEEDBACK", True)

    def _raise(result):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(analysis_service_module, "generate_feedback", _raise)

    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 200
    data = response.json()
    assert "llm_summary" not in data
